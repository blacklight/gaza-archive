import logging

import requests
from bs4 import BeautifulSoup

from ...config import Config
from ...errors import HttpError
from ...model import Account
from ._base import AccountsSource

log = logging.getLogger(__name__)


class GazaVerifiedApi(AccountsSource):  # pylint: disable=too-few-public-methods
    """
    Parser for Gaza Verified accounts
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def _extract_accounts(self, html: str) -> list[Account]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            Account(url=str(elem["href"]))
            for elem in soup.find_all(attrs={"rel": "me"})
            if elem.get("href")
            # Exclude the author of the campaign
            and str(elem.get("href", "")) not in self.config.exclude_profiles
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
