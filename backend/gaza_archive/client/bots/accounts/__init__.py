from abc import ABC
from datetime import datetime
from logging import getLogger
from threading import Thread

import requests

from ....config import Config
from ....db import Db
from ....model import Post
from ....model.suspension import SuspensionState

log = getLogger(__name__)


class MastodonAccountsBot(ABC):
    """
    Mixin for the bot that boosts new statuses of the verified accounts.
    """

    config: Config
    db: Db
    _bot_account_info: dict | None = None

    def _is_account_limited_on_home_instance(self, post: Post) -> bool:
        """
        Check if the post author is limited on their home instance.

        Returns True if the account is LIMITED on their home instance,
        False otherwise (including if no suspension data is available).
        """
        try:
            account = post.author
            account_url = account.url
            home_instance_url = account.instance_url

            # Get suspension state for the account on their home instance
            suspension_states = self.db.get_account_suspension_states(
                account_url=account_url,
                servers=[home_instance_url],
                states=[SuspensionState.LIMITED, SuspensionState.SUSPENDED],
            )

            # If we find any LIMITED state on the home instance, don't boost
            if suspension_states:
                log.info(
                    "Skipping boost for post from limited account %s on home instance %s",
                    account.fqn,
                    home_instance_url,
                )
                return True

            return False

        except Exception as e:
            # If we can't check suspension state, log the error but allow boosting
            # (fail open policy)
            log.warning(
                "Failed to check suspension state for account %s: %s. Proceeding with boost.",
                post.author.fqn,
                e,
            )
            return False

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

        # Filter out posts from accounts that are limited on their home instance
        eligible_posts = []
        for post in posts:
            if not self._is_account_limited_on_home_instance(post):
                eligible_posts.append(post)

        if len(eligible_posts) != len(posts):
            log.info(
                "Filtered out %d posts from limited accounts. Boosting %d posts.",
                len(posts) - len(eligible_posts),
                len(eligible_posts),
            )

        if not eligible_posts:
            log.info("No eligible posts to boost after filtering.")
            return

        posts = sorted(eligible_posts, key=lambda p: p.created_at or datetime.min)
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
