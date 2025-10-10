import logging

import requests

from ...config import Config
from ...errors import HttpError
from ...model import Account
from ._base import AccountsSource

log = logging.getLogger(__name__)


class MollyShahApi(AccountsSource):  # pylint: disable=too-few-public-methods
    """
    Parser for the accounts verified by `Molly Shah
    <https://bsky.app/profile/mommunism.bsky.social>`_.
    """

    # Thread containing the accounts verified by Molly Shah
    thread_url = "https://mastodon.world/api/v1/statuses/115321503465326531/context"

    # Verified account ID that posts to the thread
    account_id = "111470920259293119"

    # Known accounts to exclude
    excluded_accounts = {
        "divya",
        "raphaellakay",
    }

    def __init__(self, config: Config):
        self.config = config

    def _extract_accounts(self, posts: list[dict]) -> list[Account]:
        return [
            Account(url=mention["url"])
            for post in posts
            for mention in (post or {}).get("mentions", [])
            if (post or {}).get("account", {}).get("id") == self.account_id
            and mention.get("url")
            and all(
                f"/@{excl}" not in mention.get("url") for excl in self.excluded_accounts
            )
        ]

    def get_verified_accounts(self) -> list[Account]:
        try:
            log.info(
                "Fetching list of verified accounts from %s",
                self.thread_url,
            )
            response = requests.get(
                self.thread_url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )
            response.raise_for_status()
            accounts = self._extract_accounts(response.json()["descendants"])
            log.info("Fetched %d verified accounts", len(accounts))
            return accounts
        except requests.RequestException as exc:
            raise HttpError(
                f"Failed to fetch accounts from {self.config.accounts_source_url}"
            ) from exc
