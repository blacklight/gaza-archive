from abc import ABC
import logging

import requests
from bs4 import BeautifulSoup

from ..config import Config
from ..errors import HttpError
from ..model import Account

log = logging.getLogger(__name__)


class GazaVerifiedApi(ABC):
    """
    Parser for Gaza Verified accounts

    :param accounts_source_url: URL to fetch verified accounts from
        (default: `https://gaza-verified.org` or value of `ACCOUNTS_SOURCE_URL`
        env var)
    """

    config: Config

    def _extract_accounts(self, html: str) -> list[Account]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            Account(url=str(elem["href"]))
            for elem in soup.find_all(attrs={"rel": "me"})
            if elem.get("href")
            # Exclude the author of the campaign
            and not str(elem.get("href", "")).endswith("/@aral")
        ]

    def get_verified_accounts(self) -> list[Account]:
        try:
            log.info(
                "Fetching list of verified accounts from %s",
                self.config.accounts_source_url,
            )
            response = requests.get(
                self.config.accounts_source_url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )
            response.raise_for_status()
            accounts = self._extract_accounts(response.text)
            log.info("Fetched %d verified accounts", len(accounts))
            return accounts
        except requests.RequestException as exc:
            raise HttpError(
                f"Failed to fetch accounts from {self.config.accounts_source_url}"
            ) from exc
