import logging
import re
from datetime import datetime, timedelta, timezone
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

    # Remove a donation if it's been unconfirmed for more than an hour
    _max_unconfirmed_age = timedelta(hours=1)

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
                            status
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

    def _reconcile_from_local_window(
        self,
        campaign: Campaign,
        campaign_id: str,
        window_size: int,
    ):
        """Reconcile transient deletions using a local-db anchored overlap window.

        Strategy:
        - Take the last `window_size` local donations for this campaign
        - Query the API forward starting from the oldest local donation id
        - Consider only API donations whose timestamps overlap the local window
        - Delete local donations in that overlap window that are missing from the API
        """
        local_recent = self.db.get_recent_campaign_donations(
            campaign_url=campaign.url,
            limit=window_size,
        )

        if not local_recent:
            return

        local_min_time = min(d.created_at for d in local_recent)
        local_max_time = max(d.created_at for d in local_recent)

        # DB timestamps may be stored as offset-naive. We treat them as UTC.
        local_min_time = (
            local_min_time.replace(tzinfo=timezone.utc)
            if local_min_time.tzinfo is None
            else local_min_time.astimezone(timezone.utc)
        )

        local_max_time = (
            local_max_time.replace(tzinfo=timezone.utc)
            if local_max_time.tzinfo is None
            else local_max_time.astimezone(timezone.utc)
        )

        local_min_time_db = local_min_time.replace(tzinfo=None)
        local_max_time_db = local_max_time.replace(tzinfo=None)
        local_oldest_id = min(local_recent, key=lambda d: d.created_at).id

        # NOTE: Chuffed's GraphQL does not support last/before; this assumes `after`
        # accepts a donation id (or equivalent cursor) so we can start close to the window.
        page_cursor: str | None = local_oldest_id
        api_ids_in_window: set[str] = set()
        limit = 50

        while True:
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

                log.error(
                    "HTTP error %d fetching reconciliation donations from %s: %s",
                    response.status_code,
                    campaign.url,
                    e,
                )
                return

            data = response.json().get("data", {}).get("campaign")
            if not data:
                return

            donations_data = data.get("donations", {}).get("edges", [])
            page_info = data.get("donations", {}).get("pageInfo", {})
            if not donations_data:
                return

            page_cursor = page_info.get("endCursor")
            passed_window = False
            now = datetime.now(timezone.utc)

            for donation_edge in donations_data:
                donation_node = donation_edge.get("node") or {}
                donation_id = donation_node.get("id")
                donation_status = donation_node.get("status")
                created_at_raw = donation_node.get("createdAt")
                if not donation_id or not created_at_raw:
                    continue

                donation_time = datetime.fromisoformat(
                    created_at_raw.replace("Z", "+00:00")
                ).astimezone(timezone.utc)

                if local_min_time <= donation_time <= local_max_time and (
                    donation_status == "Confirmed"
                    or now - donation_time < self._max_unconfirmed_age
                ):
                    api_ids_in_window.add(str(donation_id))
                elif donation_time > local_max_time:
                    passed_window = True
                    break

            if passed_window or not page_info.get("hasNextPage"):
                break

        local_ids_in_window = self.db.get_campaign_donation_ids_between(
            campaign_url=campaign.url,
            start=local_min_time_db,
            end=local_max_time_db,
        )

        missing_ids = local_ids_in_window - api_ids_in_window
        deleted = self.db.delete_campaign_donations_by_ids(
            campaign_url=campaign.url,
            donation_ids=missing_ids,
        )

        if deleted:
            log.info(
                "Reconciled %d missing donations for campaign %s (window=%s..%s)",
                deleted,
                campaign.url,
                local_min_time.isoformat(),
                local_max_time.isoformat(),
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
            },
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            log.warning(
                "Cannot fetch ID for campaign %s: %s: %s",
                campaign_url,
                response.status_code,
                e,
            )
            return None

        match = re.search(r"campaignId:\s*(\d+)", response.text, re.DOTALL)
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
        donations: list[CampaignDonation] = []

        self._reconcile_from_local_window(
            campaign=campaign,
            campaign_id=campaign_id,
            window_size=20,
        )

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

                donation = CampaignDonation(
                    id=donation_node["id"],
                    url=f"{campaign.url}#donation-{donation_node['id']}",
                    campaign_url=campaign.url,
                    donor=donation_node.get("name"),
                    amount=amount,
                    created_at=donation_time,
                )
                donations.append(donation)

            if not page_info.get("hasNextPage"):
                break  # No more pages

        campaign.donations = donations
        campaign.donations_cursor = page_cursor
        return campaign
