import logging
import warnings
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from time import time

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from ....config import Config
from ....db import Db
from ....model import Account, Campaign
from ._source import CampaignSource
from .chuffed import ChuffedCampaignSource
from .gfm import GFMCampaignSource

log = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


class CampaignParser(ABC):
    config: Config
    db: Db

    def __init__(self, *_, **__):
        self.campaign_sources: set[CampaignSource] = {
            ChuffedCampaignSource(config=self.config, db=self.db),
            GFMCampaignSource(config=self.config, db=self.db),
        }

    def get_campaign_url(self, account: Account) -> str | None:
        return next(
            iter(
                [
                    self._parse_campaign_url(html)
                    for html in [account.profile_note, *account.profile_fields.values()]
                    if html
                ]
            ),
            None
        )

    def get_campaign_source(self, campaign_url: str) -> CampaignSource:
        source = next(
            iter(src for src in self.campaign_sources if src.accepts_url(campaign_url)),
            None,
        )
        assert source, f"Unsupported campaign URL: {campaign_url}"
        return source

    def refresh_campaigns(self, accounts: list[Account]) -> list[Campaign]:
        if not self.config.enable_campaign_crawlers:
            log.debug("Campaign processing is disabled.")
            return []

        log.info("Refreshing campaigns...")
        t_start = time()

        existing_campaigns = {
            account_url: campaign
            for account_url, campaign in {
                account.url: self.db.get_campaign(account.campaign_url)
                for account in accounts
                if account.campaign_url
            }.items()
            if campaign
        }

        new_campaigns = {
            account.url: Campaign(
                url=account.campaign_url,
                account_url=account.url,
                donations=[],
                donations_cursor=None,
            )
            for account in accounts
            if account.url not in existing_campaigns and account.campaign_url
        }

        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            # Refresh existing campaigns
            futures = {
                executor.submit(self.fetch_donations, campaign): url
                for url, campaign in {
                    **existing_campaigns,
                    **new_campaigns,
                }.items()
            }

            for future in futures:
                url = futures[future]
                try:
                    campaign = future.result()
                    target = existing_campaigns if url in existing_campaigns else new_campaigns
                    target[url] = campaign
                except Exception as e:
                    log.error("Error refreshing campaign %s: %s", url, e)
                    log.exception(e)

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

        soup = BeautifulSoup(html, "html.parser")
        url = next(
            iter(
                str(a["href"])  # type: ignore
                for a in soup.find_all("a")
                for campaign_source in self.campaign_sources
                if campaign_source.url_pattern.match(a.get("href", ""))  # type: ignore
            ),
            None,
        )

        if not url:
            return None

        campaign_source = next(
            (cs for cs in self.campaign_sources if cs.accepts_url(url)),
            None,
        )

        url = url.split("?", 1)[0]
        if campaign_source:
            url = campaign_source.parse_url(url)

        return url

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        campaign_source = self.get_campaign_source(campaign.url)
        donations = {
            donation.url: donation
            for donation in campaign.donations
        }

        campaign = campaign_source.fetch_donations(campaign)
        campaign.donations = sorted(
            {
                **donations,
                **({donation.url: donation for donation in list(campaign.donations)}),
            }.values(),
            key=lambda d: d.created_at,
            reverse=True,
        )

        return campaign
