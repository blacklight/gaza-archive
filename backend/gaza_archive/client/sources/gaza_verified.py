import logging

import requests

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
            accounts = [
                Account(url=account)
                for account in response.json()
            ]

            log.info("Fetched %d verified accounts", len(accounts))
            return accounts
        except requests.RequestException as exc:
            raise HttpError(
                f"Failed to fetch accounts from {self.config.accounts_source_url}"
            ) from exc
