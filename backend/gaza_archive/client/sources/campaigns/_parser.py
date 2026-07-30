import logging
import re
import warnings
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from time import time

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from ....config import Config
from ....db import Db
from ....errors import CampaignDeletedError, HttpError
from ....model import Account, Campaign, SuspensionState
from ....utils import naive_utc
from ._source import CampaignSource
from .chuffed import ChuffedCampaignSource
from .steunactie import SteunactieCampaignSource
from .gfm import GFMCampaignSource
from .whydonate import WhydonateCampaignSource

log = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class CampaignParser(ABC):
    config: Config
    db: Db

    def __init__(self, *_, **__):
        self.campaign_sources: set[CampaignSource] = {
            ChuffedCampaignSource(config=self.config, db=self.db),
            GFMCampaignSource(config=self.config, db=self.db),
            SteunactieCampaignSource(config=self.config, db=self.db),
            WhydonateCampaignSource(config=self.config, db=self.db),
        }

    def get_campaign_url(self, account: Account) -> str | None:
        return next(
            iter(
                [
                    url
                    for url in [
                        self._parse_campaign_url(html)
                        for html in [
                            account.profile_note,
                            *account.profile_fields.values(),
                        ]
                        if html
                    ]
                    if url
                ]
            ),
            None,
        )

    def get_campaign_source(self, campaign_url: str) -> CampaignSource:
        source = next(
            iter(src for src in self.campaign_sources if src.accepts_url(campaign_url)),
            None,
        )
        assert source, f"Unsupported campaign URL: {campaign_url}"
        return source

    def _get_campaigns(
        self, accounts: list[Account]
    ) -> tuple[dict[str, Campaign], dict[str, Campaign], set[str]]:
        account_urls = [account.url for account in accounts if account.campaign_url]
        home_states = self.db.get_home_instance_states(account_urls)
        for account in accounts:
            if account.state is None:
                state = home_states.get(account.url)
                account.state = state.value if state else None

        existing_campaigns: dict[str, Campaign] = {}
        new_campaigns: dict[str, Campaign] = {}
        deleted_urls: set[str] = set()

        for account in accounts:
            if not account.campaign_url:
                continue

            campaign = self.db.get_campaign(account.campaign_url)
            if campaign:
                existing_campaigns[account.url] = campaign
            else:
                new_campaigns[account.url] = Campaign(
                    url=account.campaign_url,
                    account_url=account.url,
                    donations=[],
                    donations_cursor=None,
                )

            if account.state == SuspensionState.DELETED.value:
                deleted_urls.add(account.url)
                campaign = existing_campaigns.get(account.url) or new_campaigns.get(
                    account.url
                )
                if campaign:
                    campaign.state = SuspensionState.DELETED
                    campaign.down_since = None

        return existing_campaigns, new_campaigns, deleted_urls

    def refresh_campaigns(self, accounts: list[Account]) -> list[Campaign]:
        if not self.config.enable_campaign_crawlers:
            log.debug("Campaign processing is disabled.")
            return []

        log.info("Refreshing campaigns...")
        t_start = time()
        existing_campaigns, new_campaigns, deleted_urls = self._get_campaigns(accounts)

        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            futures = {
                executor.submit(self.fetch_donations, campaign): url
                for url, campaign in {
                    **existing_campaigns,
                    **new_campaigns,
                }.items()
                if url not in deleted_urls
            }

            for future in futures:
                url = futures[future]
                campaign = existing_campaigns.get(url) or new_campaigns.get(url)
                if not campaign:
                    continue

                try:
                    refreshed = future.result()
                    refreshed.state = SuspensionState.ACTIVE
                    refreshed.down_since = None
                    target = (
                        existing_campaigns
                        if url in existing_campaigns
                        else new_campaigns
                    )
                    target[url] = refreshed
                except CampaignDeletedError as exc:
                    log.warning(str(exc))
                    campaign.state = SuspensionState.DELETED
                    campaign.down_since = None
                except HttpError as exc:
                    log.warning("Temporary error refreshing %s: %s", url, exc)
                    if campaign.down_since is None:
                        campaign.down_since = naive_utc(datetime.now(timezone.utc))
                    down_hours = (
                        naive_utc(datetime.now(timezone.utc))
                        - naive_utc(campaign.down_since)
                    ).total_seconds() / 3600
                    if down_hours > self.config.deleted_after_down_hours:
                        log.warning(
                            "Campaign %s has been unreachable for %.1f hours, marking DELETED",
                            url,
                            down_hours,
                        )
                        campaign.state = SuspensionState.DELETED
                except Exception as exc:
                    log.error("Error refreshing campaign %s: %s", url, exc)
                    log.exception(exc)

        log.info(
            "Refreshed %d campaigns in %.2f seconds.", len(accounts), time() - t_start
        )

        return list(
            {
                **existing_campaigns,
                **new_campaigns,
            }.values()
        )

    def _parse_campaign_url(self, html: str | None) -> str | None:
        if not html:
            return None

        if not re.match(r"^https?://\S+", html, re.IGNORECASE):
            # Parse HTML content
            soup = BeautifulSoup(html, "html.parser")
            url = next(
                iter(
                    str(a["href"])  # type: ignore
                    for a in soup.find_all("a")
                    for campaign_source in self.campaign_sources
                    if campaign_source.url_pattern.match(a.get("href", "").lower())  # type: ignore
                ),
                None,
            )

            if not url:
                return None
        else:
            # Direct URL
            url = html.split("?", 1)[0]

        url = url.strip().replace("Https://", "https://").split("?", 1)[0]

        campaign_source = next(
            (cs for cs in self.campaign_sources if cs.accepts_url(url)),
            None,
        )

        if not campaign_source:
            return None

        return campaign_source.parse_url(url)

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        campaign_source = self.get_campaign_source(campaign.url)
        donations = {donation.url: donation for donation in campaign.donations}
        campaign = campaign_source.fetch_donations(campaign)

        if campaign.donations:
            log.info(
                "Fetched %d new donations for account %s, campaign: %s",
                len(campaign.donations),
                campaign.account_url,
                campaign.url,
            )

        campaign.donations = sorted(
            {
                **donations,
                **({donation.url: donation for donation in campaign.donations}),
            }.values(),
            key=lambda d: d.created_at.astimezone(timezone.utc),
            reverse=True,
        )

        return campaign
