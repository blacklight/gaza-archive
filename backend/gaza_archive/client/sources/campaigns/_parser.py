import logging
import requests
from bs4 import BeautifulSoup

from ....model import Account
from ._source import CampaignSource
from .chuffed import ChuffedCampaignSource
from .gfm import GFMCampaignSource

log = logging.getLogger(__name__)


class CampaignParser:
    campaign_sources: set[CampaignSource] = {
        ChuffedCampaignSource(),
        GFMCampaignSource(),
    }

    def parse_url(self, account: Account) -> str | None:
        return self._parse_url(account.profile_note)

    def _parse_url(self, html: str | None) -> str | None:
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
            return

        # Parse any redirects
        try:
            response = requests.head(url, timeout=5)
            url = response.headers.get("Location", url)
            # Strip query parameters for clarity
        except requests.RequestException as e:
            log.warning("Error fetching campaign URL %s: %s", url, e)

        return url.split("?", 1)[0]
