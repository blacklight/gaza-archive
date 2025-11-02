import re
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import requests

from ....model.campaign import Campaign, CampaignDonation
from ._source import CampaignSource

log = getLogger(__name__)


class GFMCampaignSource(CampaignSource):
    """
    Configuration for GoFundMe campaigns.
    """

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        proxy = self.config.campaign_url_http_proxy
        self.proxies = (
            {
                "http": proxy,
                "https": proxy,
            }
            if proxy
            else {}
        )

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://(www\.)?((gofund\.me)|(gofundme\.com))/.*")

    def parse_url(self, url: str) -> str | None:
        match = re.match(
            r"^https://(www\.)?gofund\.me/([a-zA-Z0-9\-]+)",
            url,
        )

        # Parse any redirects
        if match:
            try:
                response = requests.head(
                    url,
                    proxies=self.proxies,
                    timeout=self.config.http_timeout,
                    headers={"User-Agent": self.config.user_agent},
                )
                response.raise_for_status()
                url = response.headers.get("Location", url)
            except requests.RequestException as e:
                log.warning("Error fetching campaign URL %s: %s", url, e)

        match = re.match(
            r"^https://(www\.)?gofundme\.com/f/([a-zA-Z0-9\-]+)",
            url,
        )

        if match:
            return f"https://www.gofundme.com/f/{match.group(2)}"

        return None

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

            response = requests.post(
                self._graphql_url,
                json=payload,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )

            response.raise_for_status()
            data = response.json()["data"]["fundraiser"]["donations"]
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
        if donations:
            log.info(
                "Fetched %d new donations for account %s, campaign: %s",
                len(donations),
                campaign.account_url,
                campaign.url,
            )

        return campaign
