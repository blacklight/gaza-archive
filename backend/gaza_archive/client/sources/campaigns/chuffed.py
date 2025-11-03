import logging
import re
from datetime import datetime, timezone
from textwrap import dedent
from time import sleep

import requests

from ....model.campaign import Campaign, CampaignDonation
from ._source import CampaignSource

log = logging.getLogger(__name__)


class ChuffedCampaignSource(CampaignSource):  # pylint: disable=too-few-public-methods
    """
    Configuration for Chuffed campaigns.
    """

    _graphql_url = "https://www.chuffed.org/api/graphql"
    _graphql_donation_query = dedent(
        """
        query GetCampaignDonors($campaignId: ID!, $first: Int, $after: ID) {
            campaign(id: $campaignId) {
                id title donations(first: $first, after: $after) {
                    edges {
                        node {
                            id
                            amount { amount currency }
                            name
                            createdAt
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                }
            }
        }
        """
    )

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://(www\.)?chuffed\.org/project/([a-zA-Z0-9\-]+)")

    def parse_url(self, url: str) -> str | None:
        match = self.url_pattern.match(url)
        if match:
            return f"https://www.chuffed.org/project/{match.group(2)}"

        return None

    def _get_campaign_id(self, campaign_url: str):
        response = requests.get(
            campaign_url,
            timeout=self.config.http_timeout,
            headers={
                "User-Agent": self.config.user_agent,
            }
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            log.warning(
                "Cannot fetch ID for campaign %s: %s: %s",
                campaign_url,
                response.status_code,
                e
            )
            return None

        match = re.search(r'campaignId:\s*(\d+)', response.text, re.DOTALL)
        if not match:
            log.warning("Could not parse ID for campaign %s", campaign_url)
            return None

        campaign_id = match.group(1)
        log.debug("Scraped campaign ID for %s: %s", campaign_url, campaign_id)
        return campaign_id

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        campaign_id = self._get_campaign_id(campaign.url)
        if not campaign_id:
            return campaign

        page_cursor = campaign.donations_cursor
        limit = 20
        donations = []

        while True:
            log.debug(
                "Fetching donations from %s (cursor=%s, limit=%s)",
                campaign.url,
                page_cursor,
                limit,
            )

            response = requests.post(
                self._graphql_url,
                json={
                    "query": self._graphql_donation_query,
                    "variables": {
                        "campaignId": campaign_id,
                        "first": limit,
                        "after": page_cursor,
                    },
                },
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )

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
                else:
                    log.error(
                        "HTTP error %d fetching donations from %s: %s",
                        response.status_code,
                        campaign.url,
                        e,
                    )
                    break

            data = response.json()["data"]["campaign"]
            donations_data = data["donations"]["edges"]
            page_info = data["donations"]["pageInfo"]

            if not donations_data:
                break  # No more donations to fetch

            page_cursor = page_info.get("endCursor")
            for donation_edge in donations_data:
                donation_node = donation_edge["node"]
                amount_info = donation_node["amount"]
                amount = float(amount_info["amount"]) / 100  # Convert cents to dollars
                currency = amount_info["currency"]
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
                        donor=donation_node.get("name"),
                        amount=amount,
                        created_at=donation_time,
                    )
                )

            if not page_info.get("hasNextPage"):
                break  # No more pages

        campaign.donations = donations
        campaign.donations_cursor = page_cursor
        return campaign
