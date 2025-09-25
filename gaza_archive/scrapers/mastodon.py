from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger

import requests

from ..config import Config
from ..errors import AccountNotFoundError, HttpError
from ..model import Account, Post

log = getLogger(__name__)


class MastodonApi(ABC):
    """
    Mastodon API facade.
    """

    config: Config

    def _http_get(self, url: str, *args, **kwargs) -> dict:
        """
        Perform a GET request to the Mastodon API.
        """
        response = requests.get(
            url,
            *args,
            timeout=kwargs.pop("timeout", self.config.http_timeout),
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
                **kwargs.pop("headers", {}),
            },
            **kwargs,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise HttpError(
                f"HTTP error {response.status_code} for {url}",
                status_code=response.status_code,
                exception=exc,
            ) from exc

        return response.json()

    def _get_account_id(self, account: Account) -> str:
        """
        Get the Mastodon ID of an account.
        """
        if not account.id:
            try:
                account_info = self._http_get(
                    f"{account.instanceApiUrl}/accounts/lookup",
                    params={"acct": account.username},
                )
            except HttpError as exc:
                if exc.status_code == 404:
                    raise AccountNotFoundError(
                        f"Account {account.username} not found on {account.instance}",
                        account=account.username,
                    ) from exc

                raise

            account.id = str(account_info["id"])

        return account.id

    def refresh_account(self, account: Account) -> Account:
        """
        Get the Mastodon ID of an account.
        """
        try:
            if not account.id:
                account.id = self._get_account_id(account)
        except AccountNotFoundError as exc:
            if not account.disabled:
                log.warning(str(exc))

            account.disabled = True
            return account

        account_info = self._http_get(account.apiURL)
        account.id = str(account_info["id"])
        account.display_name = account_info.get("display_name") or account.username
        account.avatar_url = account_info.get("avatar_static")
        account.header_url = account_info.get("header_static")
        account.profile_note = account_info.get("note")
        account.created_at = datetime.fromisoformat(account_info["created_at"])
        if account_info.get("locked"):
            account.disabled = account_info["locked"]

        log.debug("Refreshed account: %s", account.url)
        return account

    def refresh_accounts(self, accounts: list[Account]) -> list[Account]:
        """
        Refresh multiple accounts concurrently.
        """
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            refreshed_accounts = list(executor.map(self.refresh_account, accounts))

        return refreshed_accounts

    def refresh_account_posts(self, account: Account) -> list[Post]:
        last_fetched_id = account.last_status_id or 0

        def paginate():
            nonlocal last_fetched_id

            while True:
                response = self._http_get(
                    f"{account.apiURL}/statuses",
                    params={
                        "exclude_replies": False,
                        "exclude_reblogs": True,
                        "limit": 40,
                        "min_id": last_fetched_id,
                    },
                )

                posts = [
                    Post(
                        url=str(status["url"]),
                        id=str(status["id"]),
                        author_url=account.url,
                        content=status["content"],
                        in_reply_to_id=(
                            str(status["in_reply_to_id"])
                            if status["in_reply_to_id"]
                            else None
                        ),
                        in_reply_to_account_id=(
                            str(status["in_reply_to_account_id"])
                            if status["in_reply_to_account_id"]
                            else None
                        ),
                        created_at=datetime.fromisoformat(status["created_at"]),
                        updated_at=(
                            datetime.fromisoformat(status["edited_at"])
                            if status.get("edited_at")
                            else None
                        ),
                    )
                    for status in response
                ]

                if not posts:
                    break

                last_fetched_id = posts[0].id
                log.info(
                    "Fetched %d new posts for account %s, last_id=%s",
                    len(posts),
                    account.url,
                    last_fetched_id,
                )

                yield posts

        return list(*paginate())

    def refresh_posts(self, accounts: list[Account]) -> list[Post]:
        """
        Refresh posts for multiple accounts concurrently.
        """
        posts: dict[str, Post] = {}

        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            results = executor.map(self.refresh_account_posts, accounts)

            for batch in results:
                posts.update({post.url: post for post in batch})

        return list(posts.values())
