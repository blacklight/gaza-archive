import logging
import re
import threading
import urllib3
from abc import ABC, abstractmethod
from time import monotonic, sleep
from typing import Any
from urllib.parse import urlsplit

import requests

from ....config import Config
from ....db import Db
from ....errors import HttpError
from ....model import Campaign
from ._proxy_pool import ProxyPool


def _cffi_requests() -> Any:
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        return None
    return cffi_requests


class _CompatResponse:
    def __init__(self, response: Any) -> None:
        self._response = response

    def raise_for_status(self) -> None:
        status_code = getattr(self._response, "status_code", 200)
        if status_code >= 400:
            reason = getattr(self._response, "reason", "") or ""
            error = requests.HTTPError(f"HTTP Error {status_code}: {reason}")
            error.response = self
            raise error

    def __getattr__(self, name: str) -> Any:
        return getattr(self._response, name)


log = logging.getLogger(__name__)


class CampaignSource(ABC):
    """
    Base class for campaign sources.
    """

    #: Unique identifier of the source; used by CAMPAIGN_URL_PROXY_SOURCES to
    #: select which sources route their requests through the proxy pool.
    name: str

    def __init__(self, config: Config, db: Db, *_, **__):
        self.config = config
        self.db = db
        self._user_agent = config.campaign_user_agent or config.user_agent
        enabled_sources = {
            source.lower() for source in config.campaign_url_proxy_sources
        }
        self._proxy_pool = ProxyPool(
            proxies=(
                config.campaign_url_http_proxies
                if not enabled_sources or self.name.lower() in enabled_sources
                else []
            ),
            cooldown=config.campaign_url_proxy_cooldown,
        )
        # Max time to wait for a cooled-down proxy before giving up on the
        # request and treating it as throttled.
        self._proxy_max_wait = max(2 * config.campaign_url_proxy_cooldown, 120.0)
        self._proxy_insecure = config.campaign_url_proxy_insecure
        self._http_impersonate = config.campaign_http_impersonate
        flaresolverr_sources = {
            source.lower() for source in config.campaign_flaresolverr_sources
        }
        self._flaresolverr_url = (
            config.flaresolverr_url
            if config.flaresolverr_url
            and (not flaresolverr_sources or self.name.lower() in flaresolverr_sources)
            else None
        )
        self._flaresolverr_cache: tuple[dict[str, str], str, float] | None = None
        self._flaresolverr_lock = threading.Lock()
        self._flaresolverr_failures = 0
        if self._proxy_insecure and self._proxy_pool:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @property
    @abstractmethod
    def url_pattern(self) -> re.Pattern:
        """
        Returns the regex pattern to identify the source from a URL.
        """

    def accepts_url(self, url: str) -> bool:
        """
        Check if the source accepts the given URL.
        """
        return bool(self.url_pattern.match(url))

    def parse_url(self, url: str) -> str | None:
        """
        Parse the campaign URL from the given URL.
        """
        return url

    @abstractmethod
    def fetch_donations(self, campaign: Campaign) -> Campaign:
        """
        Fetch donations from the campaign URL.
        """

    def refresh_campaign_url(self, campaign: Campaign) -> str | None:
        """
        Try to resolve a fresh canonical URL for a campaign that appears to be
        deleted, e.g. when the upstream campaign URL changed while a shortened
        URL stayed valid. Returns the new URL, or None if none could be found.
        """
        return None

    @staticmethod
    def _retry_after(response: requests.Response) -> float | None:
        try:
            return float(response.headers["Retry-After"])
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _is_cloudflare_challenge(response: Any) -> bool:
        if (
            getattr(response, "status_code", None)
            not in HttpError.THROTTLED_STATUS_CODES
        ):
            return False

        headers = {
            str(k).lower(): v
            for k, v in (getattr(response, "headers", {}) or {}).items()
        }
        text = (getattr(response, "text", "") or "")[:5000].lower()
        return headers.get("cf-mitigated") == "challenge" or (
            "cloudflare" in headers.get("server", "").lower()
            and (
                "just a moment" in text
                or "challenges.cloudflare.com" in text
                or "cf-chl" in text
            )
        )

    def _flaresolverr_clearance(self, url: str) -> tuple[dict[str, str], str] | None:
        if not self._flaresolverr_url:
            return None
        if self._flaresolverr_cache and self._flaresolverr_cache[2] > monotonic():
            return self._flaresolverr_cache[0], self._flaresolverr_cache[1]

        with self._flaresolverr_lock:
            if self._flaresolverr_cache and self._flaresolverr_cache[2] > monotonic():
                return self._flaresolverr_cache[0], self._flaresolverr_cache[1]

            parts = urlsplit(url)
            origin = f"{parts.scheme}://{parts.netloc}/"
            endpoint = self._flaresolverr_url.rstrip("/")
            if not endpoint.endswith("/v1"):
                endpoint += "/v1"
            try:
                res = requests.post(
                    endpoint,
                    json={
                        "cmd": "request.get",
                        "url": origin,
                        "maxTimeout": 60000,
                        "returnOnlyCookies": True,
                    },
                    timeout=90,
                )
                res.raise_for_status()
                solution = res.json().get("solution") or {}
            except Exception as exc:
                log.warning("FlareSolverr clearance failed for %s: %s", url, exc)
                return None

            cookies = {
                cookie["name"]: cookie["value"]
                for cookie in (solution.get("cookies") or [])
                if cookie.get("name") and cookie.get("value")
            }
            user_agent = solution.get("userAgent")
            if "cf_clearance" not in cookies or not user_agent:
                return None

            self._flaresolverr_cache = (cookies, user_agent, monotonic() + 300)
            self._flaresolverr_failures = 0
            return cookies, user_agent

    def _request_with_clearance(
        self, method: str, url: str, kwargs: dict[str, Any]
    ) -> Any | None:
        clearance = self._flaresolverr_clearance(url)
        if not clearance:
            return None
        cookies, user_agent = clearance
        retry_kwargs = dict(kwargs)
        headers = dict(retry_kwargs.get("headers") or {})
        headers["User-Agent"] = user_agent
        retry_kwargs["headers"] = headers
        retry_kwargs["cookies"] = {
            **(retry_kwargs.get("cookies") or {}),
            **cookies,
        }
        try:
            return self._perform_request(method, url, **retry_kwargs)
        except requests.RequestException as exc:
            log.warning("FlareSolverr clearance retry failed for %s: %s", url, exc)
            return None

    def _maybe_flaresolverr(
        self, method: str, url: str, kwargs: dict[str, Any], response: Any
    ) -> Any:
        if not self._flaresolverr_url or not self._is_cloudflare_challenge(response):
            return response

        log.info("Cloudflare challenge for %s; attempting FlareSolverr", url)
        for attempt in range(2):
            solved = self._request_with_clearance(method, url, kwargs)
            if solved is None:
                break
            if not self._is_cloudflare_challenge(solved):
                self._flaresolverr_failures = 0
                log.info("FlareSolverr solved challenge for %s", url)
                return solved
            self._flaresolverr_failures += 1
            if self._flaresolverr_failures >= 3:
                self._flaresolverr_cache = None
                self._flaresolverr_failures = 0
            if attempt == 0:
                log.info(
                    "FlareSolverr clearance still challenged for %s; re-solving", url
                )

        log.warning("FlareSolverr could not solve challenge for %s", url)
        return response

    def _perform_request(
        self, method: str, url: str, proxies: dict[str, str] | None = None, **kwargs
    ) -> Any:
        request_kwargs = dict(kwargs)
        if proxies is not None:
            request_kwargs["proxies"] = proxies

        cffi = _cffi_requests()
        if self._http_impersonate and cffi is not None:
            try:
                return _CompatResponse(
                    cffi.request(
                        method,
                        url,
                        impersonate=self._http_impersonate,
                        **request_kwargs,
                    )
                )
            except Exception as exc:
                raise requests.RequestException(str(exc)) from exc

        return requests.request(method, url, **request_kwargs)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Perform an HTTP request, routing it through the configured pool of
        HTTP(S) or SOCKS proxies if one is configured.

        Proxies are selected in round-robin order. When a request through a
        proxy is throttled (401/403/429) or the proxy fails, the proxy is put
        in cool-down and the next available proxy is tried. If every proxy is
        cooling down, wait for the soonest one up to a bounded maximum;
        afterwards the last response is returned so that the caller can apply
        its usual throttling handling.
        """
        pool = self._proxy_pool
        if not pool:
            response = self._perform_request(method, url, **kwargs)
            return self._maybe_flaresolverr(method, url, kwargs, response)

        if self._proxy_insecure:
            kwargs.setdefault("verify", False)

        attempts = 0
        max_attempts = 2 * len(pool)
        waited = 0.0
        response: requests.Response | None = None
        last_error: requests.RequestException | None = None
        solver_tried = False

        while attempts < max_attempts:
            proxy = pool.acquire()
            if proxy is None:
                wait = pool.cooldown_remaining()
                if waited + wait > self._proxy_max_wait:
                    break
                log.info(
                    "All %d proxies are cooling down, waiting %.0f seconds...",
                    len(pool),
                    wait,
                )
                sleep(wait)
                waited += wait
                continue

            attempts += 1
            try:
                response = self._perform_request(
                    method,
                    url,
                    proxies={"http": proxy, "https": proxy},
                    **kwargs,
                )
                last_error = None
            except requests.RequestException as e:
                log.warning("Request via proxy failed: %s", e)
                pool.report_failure(proxy)
                last_error = e
                continue

            if (
                not solver_tried
                and self._flaresolverr_url
                and self._is_cloudflare_challenge(response)
            ):
                solver_tried = True
                response = self._maybe_flaresolverr(method, url, kwargs, response)

            if response.status_code in HttpError.THROTTLED_STATUS_CODES:
                log.warning(
                    "Request via proxy was throttled (%d), trying next proxy",
                    response.status_code,
                )
                pool.report_rate_limited(proxy, self._retry_after(response))
                continue

            return response

        if response is not None and last_error is None:
            return response

        raise HttpError(
            "All proxies are rate-limited or unavailable",
            status_code=429,
            exception=last_error,
        )
