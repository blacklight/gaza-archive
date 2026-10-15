import re
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

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

    _graphql_url = "https://graphql.gofundme.com/graphql"
    _graphql_donation_query = """
query GetFundraiserDonations(
    $slug: ID!,
    $first: Int,
    $last: Int,
    $before: String,
    $after: String,
    $order: DonationOrder
) {
  fundraiser(slug: $slug) {
    id
    donations(
      first: $first
      last: $last
      before: $before
      after: $after
      order: $order
    ) {
      edges {
        node {
          ...FundraiserDonationFields
          __typename
        }
        __typename
      }
      pageInfo {
        startCursor
        endCursor
        hasNextPage
        hasPreviousPage
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment FundraiserDonationFields on Donation {
  amount {
    amount
    currencyCode
    __typename
  }
  checkoutId
  createdAt
  fundraiser {
    id
    __typename
  }
  id
  isAnonymous
  isOffline
  isRecurring
  isVerified
  name
  profileUrl
  donorProfile {
    id
    mode
    slug
    status
    __typename
  }
  __typename
}
    """.strip()

    _short_url_pattern = re.compile(r"^https://(www\.)?gofund\.me/([a-zA-Z0-9\-]+)")
    _canonical_url_pattern = re.compile(
        r"^https://(www\.)?gofundme\.com/f/([a-zA-Z0-9\-]+)"
    )

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://(www\.)?((gofund\.me)|(gofundme\.com))/.*")

    def _resolve_short_url(self, short_url: str) -> str | None:
        """
        Resolve a gofund.me short URL to its canonical gofundme.com campaign
        URL by following the redirect.
        """
        try:
            response = self._request(
                "HEAD",
                short_url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self._user_agent},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            log.warning("Error fetching campaign URL %s: %s", short_url, e)
            return None

        url = response.headers.get("Location", short_url)
        match = self._canonical_url_pattern.match(url)
        if match:
            return f"https://www.gofundme.com/f/{match.group(2)}"

        return None

    def parse_url(self, url: str) -> str | None:
        match = self._short_url_pattern.match(url)

        # gofund.me short URLs resolve to the canonical campaign URL with a
        # redirect. The resolver is slow, so resolutions are cached; a stale
        # cache entry (e.g. after a campaign slug rename) is refreshed by
        # refresh_campaign_url() when the canonical URL stops working.
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

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        """
        Fetch donations from the campaign URL.
        """
        page_cursor = None
        start_cursor = campaign.donations_cursor
        end_cursor = campaign.donations_cursor
        limit = 20
        donations = []

        while True:
            log.debug(
                "Fetching donations from %s (cursor=%s, limit=%s)",
                campaign.url,
                end_cursor,
                limit,
            )

            payload: dict[str, Any] = {
                "operationName": "GetFundraiserDonations",
                "variables": {
                    "slug": campaign.url.rstrip("/").split("/")[-1],
                },
                "query": self._graphql_donation_query,
            }

            if campaign.donations_cursor:
                # Start from the latest fetched donation and go towards the present if the cursor is set
                payload["variables"]["after"] = start_cursor
                payload["variables"]["first"] = limit
            else:
                # Otherwise, go backwards from the most recent donation
                payload["variables"]["before"] = end_cursor
                payload["variables"]["last"] = limit

            response = self._request(
                "POST",
                self._graphql_url,
                json=payload,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self._user_agent},
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
                if (
                    response.status_code in (404, 410)
                    or 400 <= response.status_code < 500
                ):
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

            fundraiser = response.json().get("data", {}).get("fundraiser")
            if not fundraiser:
                raise CampaignDeletedError(
                    f"Campaign {campaign.url} has no fundraiser data",
                    campaign_url=campaign.url,
                    status_code=404,
                )

            data = fundraiser.get("donations", {}) or {}
            donations_data = data.get("edges", [])
            start_cursor = data.get("pageInfo", {}).get("startCursor")
            end_cursor = data.get("pageInfo", {}).get("endCursor")
            if start_cursor and (campaign.donations_cursor or not page_cursor):
                page_cursor = start_cursor

            if not end_cursor:
                break

            for donation_edge in donations_data:
                donation_node = donation_edge["node"]
                amount_info = donation_node["amount"]
                amount = float(amount_info["amount"])
                currency = amount_info["currencyCode"]
                donation_time = datetime.fromisoformat(
                    donation_node["createdAt"].replace("Z", "+00:00")
                ).astimezone(timezone.utc)

                if currency != "USD":
                    amount = self.db.convert(
                        amount=amount,
                        from_currency=currency,
                        to_currency="USD",
                        date=donation_time.date().strftime("%Y-%m-%d"),
                    )["converted_amount"]

                donations.append(
                    CampaignDonation(
                        id=donation_node["id"],
                        url=f"{campaign.url}#donation-{donation_node['id']}",
                        campaign_url=campaign.url,
                        amount=amount,
                        created_at=donation_time,
                        donor=(
                            donation_node["name"]
                            if not donation_node["isAnonymous"]
                            else None
                        ),
                    )
                )

        campaign.donations = donations
        campaign.donations_cursor = page_cursor
        return campaign
