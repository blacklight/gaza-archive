import logging
import re
import urllib3
from abc import ABC, abstractmethod
from time import sleep

import requests

from ....config import Config
from ....db import Db
from ....errors import HttpError
from ....model import Campaign
from ._proxy_pool import ProxyPool

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
            return requests.request(method, url, **kwargs)

        if self._proxy_insecure:
            kwargs.setdefault("verify", False)

        attempts = 0
        max_attempts = 2 * len(pool)
        waited = 0.0
        response: requests.Response | None = None
        last_error: requests.RequestException | None = None

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
                response = requests.request(
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
