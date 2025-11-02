from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger

import requests

from ..config import Config
from ..errors import AccountNotFoundError, HttpError
from ..model import Account, Media, Post
from .sources.campaigns import CampaignParser

log = getLogger(__name__)


class MastodonApi(ABC):
    """
    Mastodon API facade.
    """

    config: Config
    campaign_parser: CampaignParser

    def _http_get(self, url: str, *args, **kwargs) -> dict:
        """
        Perform a GET request to the Mastodon API.
        """
        while True:
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
                return response.json()
            except requests.ConnectionError as exc:
                raise HttpError(
                    f"Connection error for {url}",
                    exception=exc,
                ) from exc
            except requests.HTTPError as exc:
                if response.status_code == 429:
                    rate_limit_reset_date = response.headers.get("X-RateLimit-Reset")
                    if rate_limit_reset_date:
                        reset_timestamp = datetime.fromisoformat(
                            re.sub(r"Z$", "+00:00", rate_limit_reset_date)
                        ).timestamp()
                    else:
                        reset_timestamp = datetime.now().timestamp() + 10

                    sleep_seconds = int(max(0., reset_timestamp - datetime.now().timestamp()) + 1)
                    log.warning(
                        "Rate limit exceeded for %s, sleeping for %d seconds...",
                        url,
                        sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
                else:
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

    def get_campaign_url(self, account: Account) -> str | None:
        """
        Get the campaign URL from the account's profile note.
        """
        if not account.profile_note:
            return None

        return self.campaign_parser.parse_url(account) or None

    def _convert_datetime(self, value: str) -> datetime | None:
        if not value:
            return None

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        return datetime.fromisoformat(value)

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
        account.campaign_url = self.get_campaign_url(account)
        account.created_at = self._convert_datetime(account_info["created_at"])
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
            return list(executor.map(self.refresh_account, accounts))

    def refresh_account_posts(self, account: Account) -> list[Post]:
        last_fetched_id = account.last_status_id or 0

        def paginate():
            nonlocal last_fetched_id

            while True:
                response = self._http_get(
                    f"{account.apiURL}/statuses",
                    params={
                        "exclude_replies": int(False),
                        "exclude_reblogs": int(True),
                        "limit": 40,
                        "min_id": last_fetched_id,
                    },
                )

                posts_by_url = {
                    str(status["url"]): Post(
                        url=str(status["url"]),
                        id=str(status["id"]),
                        author=account,
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
                        created_at=self._convert_datetime(status["created_at"]),
                        updated_at=(
                            self._convert_datetime(status["edited_at"])
                            if status.get("edited_at")
                            else None
                        ),
                    )
                    for status in response
                }

                for status in response:
                    post = posts_by_url[str(status["url"])]
                    post.attachments = [
                        Media(
                            url=media["url"],
                            id=str(media["id"]),
                            type=media.get("type"),
                            description=media.get("description"),
                            post=post,
                        )
                        for media in status.get("media_attachments", [])
                    ]

                if not posts_by_url:
                    break

                posts = sorted(posts_by_url.values(), key=lambda p: int(p.id))
                last_fetched_id = posts[-1].id
                log.info(
                    "Fetched %d new posts for account %s, last_id=%s",
                    len(posts),
                    account.url,
                    last_fetched_id,
                )

                yield posts

        return [post for batch in paginate() for post in batch]

    def refresh_posts(self, accounts: list[Account]) -> list[Post]:
        """
        Refresh posts for multiple accounts concurrently.
        """
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            results = executor.map(
                self.refresh_account_posts,
                [account for account in accounts if not account.disabled],
            )

            return list(
                {post.url: post for batch in results for post in batch}.values()
            )
