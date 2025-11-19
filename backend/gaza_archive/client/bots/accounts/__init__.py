from abc import ABC
from logging import getLogger
from threading import Thread

import requests

from ....config import Config
from ....model import Post

log = getLogger(__name__)


class MastodonAccountsBot(ABC):
    """
    Mixin for the bot that boosts new statuses of the verified accounts.
    """

    config: Config
    _bot_account_info: dict | None = None

    @property
    def __is_enabled(self):
        return (
            self.config.mastodon_accounts_bot_instance_url
            and self.config.mastodon_accounts_bot_access_token
        )

    @property
    def __api_url(self) -> str:
        return f"{self.config.mastodon_accounts_bot_instance_url}/api"

    @property
    def __request_args(self) -> dict:
        return {
            "headers": {
                "Authorization": f"Bearer {self.config.mastodon_accounts_bot_access_token}"
            },
            "timeout": self.config.http_timeout,
        }

    @property
    def bot_account_info(self) -> dict | None:
        if not self._bot_account_info:
            self._update_accounts_bot_info()
        return self._bot_account_info

    def _update_accounts_bot_info(self) -> None:
        if not self.__is_enabled:
            return

        try:
            response = requests.get(
                f"{self.__api_url}/v1/accounts/verify_credentials",
                **self.__request_args,
            )
            response.raise_for_status()
            self._bot_account_info = response.json()
            assert self._bot_account_info, "Bot account info is empty"
        except Exception as e:
            log.error("Failed to verify Mastodon bot account: %s", e)
            self._bot_account_info = None

    def __get_local_status_id(self, post: Post) -> str:
        """
        Get the local status ID for a given post URL.

        If the status wasn't posted on the same instance as the bot, it performs a search.
        """
        bot_instance = self.config.mastodon_accounts_bot_instance_url
        account_instance = "https://" + post.author.fqn.split("@")[-1]
        if bot_instance == account_instance:
            return post.id

        response = requests.get(
            f"{self.__api_url}/v2/search",
            params={
                "q": post.url,
                "type": "statuses",
                "limit": 1,
                "resolve": "true",
            },
            **self.__request_args,
        )
        response.raise_for_status()
        search_results = response.json()
        statuses = search_results.get("statuses", [])
        if not statuses:
            raise ValueError(f"Status not found in search: {post.url}")

        return statuses[0]["id"]

    def _boost_posts(self, posts: list[Post]) -> None:
        if not self.bot_account_info:
            log.error("Cannot boost posts: bot account info is not available.")
            return

        posts = sorted(posts, key=lambda p: p.created_at or 0)
        log.info("Boosting %d new posts...", len(posts))

        for post in posts:
            try:
                post_id = self.__get_local_status_id(post)
                response = requests.post(
                    f"{self.__api_url}/v1/statuses/{post_id}/reblog",
                    **self.__request_args,
                )
                response.raise_for_status()
                log.info("Boosted post: %s", post.url)
            except Exception as e:
                log.error("Failed to boost post %s: %s", post.url, e)

    def boost_posts(self, posts: list[Post]) -> None:
        """
        Boost new posts of the verified accounts (in a separate thread).
        """
        if not (self.__is_enabled and posts):
            return

        Thread(target=self._boost_posts, args=(posts,), daemon=True).start()