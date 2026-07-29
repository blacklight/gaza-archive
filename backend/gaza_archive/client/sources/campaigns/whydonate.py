import logging
import re
from datetime import datetime, timezone
from time import sleep
from typing import Any

import requests

from ....model.campaign import Campaign, CampaignDonation
from ._source import CampaignSource

log = logging.getLogger(__name__)


# WhyDonate's public donation API reports only the currency *symbol*, not the
# ISO code. This mapping covers the most common symbols. Ambiguous symbols
# (e.g. ``$``) are resolved against the campaign's own currency when possible.
_SYMBOL_TO_CURRENCY: dict[str, str] = {
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₽": "RUB",
    "₩": "KRW",
    "₺": "TRY",
    "R$": "BRL",
    "₱": "PHP",
    "₫": "VND",
    "₪": "ILS",
    "฿": "THB",
    "₴": "UAH",
    "₨": "PKR",
    "₦": "NGN",
    "A$": "AUD",
    "C$": "CAD",
    "S$": "SGD",
    "HK$": "HKD",
    "NZ$": "NZD",
    "kr": "SEK",
    "zł": "PLN",
    "Kč": "CZK",
    "Ft": "HUF",
    "CHF": "CHF",
    "R": "ZAR",
    "د.إ": "AED",
    "ر.س": "SAR",
    "₾": "GEL",
    "₸": "KZT",
    "؋": "AFN",
    "৳": "BDT",
    "₮": "MNT",
    "lei": "RON",
    "$": "USD",
}

_ANONYMOUS_NAMES = {
    "anonymous",
    "anoniem",
    "anónimo",
    "anonyme",
    "anonym",
    "onbekend",
    "",
}


class WhydonateCampaignSource(CampaignSource):  # pylint: disable=too-few-public-methods
    """
    Configuration for whydonate.com / whydonate.in campaigns.
    """

    _fundraiser_api_url = "https://fundraiser.whydonate.dev/fundraiser/get"
    _donations_api_url = (
        "https://donation.whydonate.dev/donation/orders/fundraising/local/"
    )
    _page_limit = 20

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(
            r"^https://(www\.)?whydonate\.(com|in)(/[a-z]{2})?/fundraising/([a-zA-Z0-9\-]+)"
        )

    def parse_url(self, url: str) -> str | None:
        match = self.url_pattern.match(url)
        if match:
            slug = match.group(4)
            return f"https://whydonate.com/fundraising/{slug}"

        return None

    def _get_fundraiser_info(self, slug: str) -> dict[str, Any] | None:
        """Fetch public fundraiser metadata, including the campaign currency."""
        response = requests.get(
            self._fundraiser_api_url,
            params={"slug": slug, "language": "en"},
            timeout=self.config.http_timeout,
            headers={"User-Agent": self.config.user_agent},
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            log.warning(
                "Cannot fetch fundraiser info for %s: %s: %s",
                slug,
                response.status_code,
                e,
            )
            return None

        result = response.json().get("data", {}).get("result")
        if not result:
            log.warning("Could not parse fundraiser info for %s", slug)
            return None

        return result

    @staticmethod
    def _currency_from_fundraiser(
        symbol: str, fundraiser_info: dict[str, Any] | None
    ) -> str | None:
        """Return the fundraiser's currency code if the symbol matches it."""
        if not fundraiser_info:
            return None

        info_symbol = (fundraiser_info.get("currency_symbol") or "").strip()
        info_currency = (fundraiser_info.get("currency_code") or "").strip()
        if symbol and info_symbol and symbol == info_symbol and info_currency:
            return info_currency.upper()

        return None

    def _symbol_to_currency(
        self, symbol: str | None, fundraiser_info: dict[str, Any] | None
    ) -> str:
        """Map a currency symbol to an ISO 4217 currency code."""
        symbol = (symbol or "").strip()

        currency = self._currency_from_fundraiser(symbol, fundraiser_info)
        if currency:
            return currency

        if symbol in _SYMBOL_TO_CURRENCY:
            return _SYMBOL_TO_CURRENCY[symbol]

        # Fallback: use the campaign currency if the symbols match loosely.
        if fundraiser_info:
            info_currency = (fundraiser_info.get("currency_code") or "").strip()
            if info_currency:
                return info_currency.upper()

        log.warning(
            "Unknown currency symbol %r for whydonate campaign; defaulting to USD",
            symbol,
        )
        return "USD"

    def _build_donation(
        self,
        donation: dict[str, Any],
        fundraiser_info: dict[str, Any] | None,
        campaign: Campaign,
        scrape_time: datetime,
    ) -> CampaignDonation | None:
        """Convert a raw whydonate donation record into a CampaignDonation."""
        donation_id = donation.get("id")
        if not donation_id:
            return None

        amount_str = donation.get("amount") or "0"
        amount = float(amount_str)

        symbol = donation.get("symbol")
        currency = self._symbol_to_currency(symbol, fundraiser_info)

        # The public API does not expose donation timestamps, so we use the
        # scraping time as an approximation of the donation date.
        created_at = scrape_time

        if currency != "USD":
            amount = self.db.convert(
                amount=amount,
                from_currency=currency,
                to_currency="USD",
                date=created_at.date().isoformat(),
            )["converted_amount"]

        donor = (donation.get("name") or "").strip()
        if donor.lower() in _ANONYMOUS_NAMES:
            donor = None

        return CampaignDonation(
            id=str(donation_id),
            url=f"{campaign.url}#donation-{donation_id}",
            campaign_url=campaign.url,
            amount=amount,
            created_at=created_at,
            donor=donor,
        )

    def _fetch_page(self, slug: str, page: int) -> requests.Response:
        """Fetch one page of donations from the public whydonate API."""
        return requests.get(
            self._donations_api_url,
            params={
                "slug": slug,
                "page": page,
                "limit": self._page_limit,
                "language_code": "en",
            },
            timeout=self.config.http_timeout,
            headers={"User-Agent": self.config.user_agent},
        )

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        match = self.url_pattern.match(campaign.url)
        if not match:
            log.warning("Cannot parse slug from whydonate URL %s", campaign.url)
            return campaign

        slug = match.group(4)
        fundraiser_info = self._get_fundraiser_info(slug)

        last_id = int(campaign.donations_cursor or "0")
        page = 1
        donations: list[CampaignDonation] = []
        new_max_id = last_id
        scrape_time = datetime.now(timezone.utc)

        while True:
            log.debug(
                "Fetching donations from %s (page=%d, limit=%s, cursor=%s)",
                campaign.url,
                page,
                self._page_limit,
                last_id,
            )

            response = self._fetch_page(slug, page)

            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                if response.status_code == 429:
                    sleep_seconds = int(response.headers.get("Retry-After", "10")) + 1
                    log.warning(
                        "Rate limit exceeded for %s, sleeping for %d seconds...",
                        campaign.url,
                        sleep_seconds,
                    )
                    sleep(sleep_seconds)
                    continue

                log.error(
                    "HTTP error %d fetching donations from %s: %s",
                    response.status_code,
                    campaign.url,
                    e,
                )
                break

            data = response.json().get("data", {}).get("result", {})
            donations_data = data.get("result", [])

            if not donations_data:
                break

            passed_cursor = False

            for donation in donations_data:
                donation_id = int(donation.get("id", 0))

                if donation_id <= last_id:
                    passed_cursor = True
                    break

                new_max_id = max(new_max_id, donation_id)

                campaign_donation = self._build_donation(
                    donation,
                    fundraiser_info,
                    campaign,
                    scrape_time,
                )
                if campaign_donation:
                    donations.append(campaign_donation)

            if passed_cursor or len(donations_data) < self._page_limit:
                break

            page += 1

        # The public API already returns donations ordered by id descending, but
        # we make the ordering explicit and robust.
        donations.sort(key=lambda d: int(d.id), reverse=True)

        campaign.donations = donations
        campaign.donations_cursor = str(new_max_id)
        return campaign
