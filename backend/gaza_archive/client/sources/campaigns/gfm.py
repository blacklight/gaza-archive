import re
import threading
from datetime import datetime, timezone
from logging import getLogger
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

import requests

from ....errors import CampaignDeletedError, HttpError
from ....model.campaign import Campaign, CampaignDonation
from ._source import CampaignSource

log = getLogger(__name__)


class GFMCampaignSource(CampaignSource):
    """
    Configuration for GoFundMe campaigns.
    """

    name = "gofundme"

    _donations_url = "https://gateway.gofundme.com/web-gateway/v1/feed/{slug}/donations"
    _page_limit = 100
    _max_pages = 10
    _short_url_timeout = 5
    _short_url_negative_cache_ttl = 1800

    _short_url_pattern = re.compile(r"^https://(www\.)?gofund\.me/([a-zA-Z0-9\-]+)")
    _canonical_url_pattern = re.compile(
        r"^https://(www\.)?gofundme\.com/f/([a-zA-Z0-9\-]+)"
    )

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://(www\.)?((gofund\.me)|(gofundme\.com))/.*")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._short_url_lock = threading.Lock()
        self._short_url_negative_cache: dict[str, float] = {}

    def _resolve_short_url(self, short_url: str) -> str | None:
        """
        Resolve a gofund.me short URL to its canonical gofundme.com campaign
        URL by following the redirect.
        """
        if self._short_url_negative_cache.get(short_url, 0) > monotonic():
            return None

        with self._short_url_lock:
            if self._short_url_negative_cache.get(short_url, 0) > monotonic():
                return None

            try:
                response = self._request(
                    "GET",
                    short_url,
                    timeout=self._short_url_timeout,
                    headers={
                        "User-Agent": self._user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                    allow_redirects=False,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                self._short_url_negative_cache[short_url] = (
                    monotonic() + self._short_url_negative_cache_ttl
                )
                raise HttpError(
                    f"Error fetching campaign URL {short_url}",
                    status_code=503,
                    exception=e,
                ) from e

            self._short_url_negative_cache.pop(short_url, None)
            url = response.headers.get("Location", short_url)
            match = self._canonical_url_pattern.match(url)
            if match:
                return f"https://www.gofundme.com/f/{match.group(2)}"

            self._short_url_negative_cache[short_url] = (
                monotonic() + self._short_url_negative_cache_ttl
            )
            return None

    def parse_url(self, url: str) -> str | None:
        match = self._short_url_pattern.match(url)

        # gofund.me short URLs resolve to the canonical campaign URL with a
        # redirect. The resolver is slow, so resolutions and recent failures
        # are cached; a stale cache entry (e.g. after a campaign slug rename)
        # is refreshed by refresh_campaign_url() when the canonical URL stops
        # working.
        if match:
            short_url = f"https://gofund.me/{match.group(2)}"
            cached = self.db.get_campaign_url_cache(short_url)
            if cached:
                return cached
            try:
                resolved = self._resolve_short_url(short_url)
            except HttpError as e:
                log.warning("Error fetching campaign URL %s: %s", short_url, e)
                return None
            if resolved:
                self.db.set_campaign_url_cache(short_url, resolved)
            return resolved

        match = self._canonical_url_pattern.match(url)
        if match:
            return f"https://www.gofundme.com/f/{match.group(2)}"

        return None

    def refresh_campaign_url(self, campaign: Campaign) -> str | None:
        """
        Re-resolve the gofund.me short URL this campaign was discovered
        through, in case its canonical URL changed (slug rename).
        """
        short_url = self.db.get_campaign_url_source(campaign.url)
        if not short_url:
            return None
        resolved = self._resolve_short_url(short_url)
        if not resolved or resolved == campaign.url:
            return None
        self.db.set_campaign_url_cache(short_url, resolved)
        return resolved

    def _campaign_slug(self, campaign: Campaign) -> str:
        return urlsplit(campaign.url).path.rstrip("/").rsplit("/", 1)[-1]

    def _fetch_donations_page(
        self, campaign: Campaign, offset: int
    ) -> tuple[list[dict[str, Any]], bool]:
        response = self._request(
            "GET",
            self._donations_url.format(slug=self._campaign_slug(campaign)),
            params={
                "limit": self._page_limit,
                "offset": offset,
                "sort": "recent",
            },
            timeout=self.config.http_timeout,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "application/json",
            },
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code in HttpError.THROTTLED_STATUS_CODES:
                raise HttpError(
                    f"Campaign {campaign.url} access denied: {response.status_code}",
                    status_code=response.status_code,
                    exception=e,
                ) from e
            if response.status_code in (404, 410) or 400 <= response.status_code < 500:
                raise CampaignDeletedError(
                    f"Campaign {campaign.url} not found: {response.status_code}",
                    campaign_url=campaign.url,
                    status_code=response.status_code,
                ) from e
            if response.status_code >= 500:
                raise HttpError(
                    f"Server error fetching donations from {campaign.url}",
                    status_code=response.status_code,
                    exception=e,
                ) from e
            raise
        except requests.RequestException as e:
            raise HttpError(
                f"Connection error fetching donations from {campaign.url}",
                status_code=503,
                exception=e,
            ) from e

        try:
            payload = response.json()
        except ValueError as e:
            raise HttpError(
                f"Invalid response fetching donations from {campaign.url}",
                status_code=502,
                exception=e,
            ) from e
        if not isinstance(payload, dict):
            raise HttpError(
                f"Invalid response fetching donations from {campaign.url}",
                status_code=502,
            )

        references = payload.get("references")
        meta = payload.get("meta")
        donations = (
            references.get("donations", []) if isinstance(references, dict) else []
        )
        if not isinstance(donations, list):
            raise HttpError(
                f"Invalid response fetching donations from {campaign.url}",
                status_code=502,
            )
        has_next = bool(meta.get("has_next")) if isinstance(meta, dict) else False
        return donations, has_next

    def _build_donation(
        self, campaign: Campaign, donation: dict[str, Any]
    ) -> CampaignDonation | None:
        donation_id = donation.get("donation_id")
        created_at = donation.get("created_at")
        amount = donation.get("amount")
        if donation_id is None or created_at is None or amount is None:
            return None

        donation_id = str(donation_id)
        try:
            donation_time = datetime.fromisoformat(
                str(created_at).replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            value = float(amount)
        except (TypeError, ValueError):
            log.warning("Skipping malformed GoFundMe donation %s", donation_id)
            return None

        currency = str(donation.get("currencycode") or "USD").upper()
        if currency != "USD":
            value = self.db.convert(
                amount=value,
                from_currency=currency,
                to_currency="USD",
                date=donation_time.date().strftime("%Y-%m-%d"),
            )["converted_amount"]

        return CampaignDonation(
            id=donation_id,
            url=f"{campaign.url}#donation-{donation_id}",
            campaign_url=campaign.url,
            amount=value,
            created_at=donation_time,
            donor=(
                None if donation.get("is_anonymous") else (donation.get("name") or None)
            ),
        )

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        """
        Fetch donations from the campaign URL.
        """
        known_ids = {str(donation.id) for donation in campaign.donations}
        donations: list[CampaignDonation] = []
        offset = 0

        for _ in range(self._max_pages):
            log.debug(
                "Fetching donations from %s (offset=%d, limit=%d)",
                campaign.url,
                offset,
                self._page_limit,
            )

            rows, has_next = self._fetch_donations_page(campaign, offset)
            if not rows:
                break

            page_has_known = False
            page_has_new = False
            for row in rows:
                if not isinstance(row, dict):
                    continue
                raw_id = row.get("donation_id")
                row_id = str(raw_id) if raw_id is not None else None
                if row_id is not None and row_id in known_ids:
                    page_has_known = True
                else:
                    page_has_new = True

                donation = self._build_donation(campaign, row)
                if donation:
                    donations.append(donation)

            offset += self._page_limit
            if not has_next or len(rows) < self._page_limit:
                break
            if page_has_known and not page_has_new:
                break

        campaign.donations = donations
        campaign.donations_cursor = None
        return campaign
