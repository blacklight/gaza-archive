from abc import ABC
from datetime import datetime, timedelta, timezone
from logging import getLogger
from threading import Event, Thread

import requests

from ....config import Config
from ....db import Db
from ....model import CampaignAccountStats

log = getLogger(__name__)


class MastodonCampaignsBot(ABC):
    """
    Mixin for the bot that periodically posts underfunded campaigns to Mastodon.
    """

    config: Config
    db: Db

    _bot_campaign_info: dict | None = None
    _bot_campaign_thread: Thread | None = None
    _bot_campaign_stop_event = Event()
    __bot_name = "mastodon_campaigns_bot"
    _post_header_template = "#GazaVerified campaigns that raised less than ${min_amount} in the past {time_window} days:\n\n"
    _max_post_length: int = (
        500 - len("\n\n(10/10)") - 2
    )  # Reserve space for (m/n) indicators

    @property
    def __is_enabled(self) -> bool:
        return bool(
            self.config.mastodon_campaigns_bot_instance_url
            and self.config.mastodon_campaigns_bot_access_token
        )

    @property
    def __api_url(self) -> str:
        return f"{self.config.mastodon_campaigns_bot_instance_url}/api"

    @property
    def __request_args(self) -> dict:
        return {
            "headers": {
                "Authorization": f"Bearer {self.config.mastodon_campaigns_bot_access_token}"
            },
            "timeout": self.config.http_timeout,
        }

    @property
    def bot_campaign_info(self) -> dict | None:
        if not self._bot_campaign_info:
            self._update_campaigns_bot_info()
        return self._bot_campaign_info

    def _update_campaigns_bot_info(self) -> None:
        if not self.__is_enabled:
            return

        try:
            response = requests.get(
                f"{self.__api_url}/v1/accounts/verify_credentials",
                **self.__request_args,
            )
            response.raise_for_status()
            self._bot_campaign_info = response.json()
            assert self._bot_campaign_info, "Bot campaign info is empty"
        except Exception as e:
            log.error("Failed to verify Mastodon bot account: %s", e)
            self._bot_campaign_info = None

    def get_underfunded_campaigns(self) -> list[CampaignAccountStats]:
        if not self.__is_enabled:
            return []

        time_window_days = self.config.mastodon_campaigns_bot_time_window_days
        max_amount = self.config.mastodon_campaigns_bot_min_raise_amount
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        campaigns_stats = self.db.get_campaigns(
            start_time=cutoff_date,
            group_by=["account.url"],
        )
        return sorted(  # type: ignore
            [
                campaign
                for campaign in campaigns_stats.data
                if campaign.amount.amount < max_amount
            ],
            key=lambda c: c.amount.amount,
        )

    def _to_posts(self, campaigns: list[CampaignAccountStats]) -> list[str]:
        posts = []
        current_post = ""
        for i, campaign_stats in enumerate(campaigns):
            line = f"{i + 1}. {campaign_stats.account.fqn} (${int(round(campaign_stats.amount.amount))})\n"
            if len(current_post) + len(line) > self._max_post_length:
                posts.append(current_post.strip())
                current_post = line
            else:
                current_post += line

        if current_post:
            posts.append(current_post.strip())

        # Add (m/n) indicators if there are multiple posts
        total_posts = len(posts)
        for i, post in enumerate(posts):
            posts[i] = (
                self._post_header_template.format(
                    min_amount=self.config.mastodon_campaigns_bot_min_raise_amount,
                    time_window=self.config.mastodon_campaigns_bot_time_window_days,
                )
                + post.strip()
                + (f"\n\n({i + 1}/{total_posts})" if total_posts > 1 else "")
            )

        return posts

    def _submit_posts(self, posts: list[str]) -> None:
        last_post_id = None

        for i, post in enumerate(posts):
            try:
                response = requests.post(
                    f"{self.__api_url}/v1/statuses",
                    json={
                        "status": post,
                        "in_reply_to_id": last_post_id,
                    },
                    **self.__request_args,
                )
                response.raise_for_status()
                last_post_id = response.json().get("id")
            except Exception as e:
                log.error("Failed to post campaign update to Mastodon: %s", e)
                log.exception(e)

        if last_post_id is not None:
            log.info(
                "Successfully posted %d campaign updates. Last post ID: %s",
                len(posts),
                last_post_id,
            )

    def _campaigns_bot_main(self):
        poll_interval = self.config.mastodon_campaigns_bot_post_interval_hours
        bot_state = self.db.get_bot_state(self.__bot_name)
        latest_update = (
            bot_state.last_updated_at.astimezone(timezone.utc)
            if bot_state and bot_state.last_updated_at
            else datetime.min.replace(tzinfo=timezone.utc)
        )

        initial_wait = (
            latest_update + timedelta(hours=poll_interval) - datetime.now(timezone.utc)
        ).total_seconds()
        if initial_wait > 0:
            log.info(
                "Mastodon campaigns bot waiting for %.2f seconds before first run.",
                initial_wait,
            )
            self._bot_campaign_stop_event.wait(initial_wait)

        while not self._bot_campaign_stop_event.is_set():
            try:
                underfunded_campaigns = self.get_underfunded_campaigns()
                posts = self._to_posts(underfunded_campaigns)
                if posts:
                    self._submit_posts(posts)
                else:
                    log.info("No underfunded campaigns to post.")

                self.db.refresh_bot_state(self.__bot_name)
            except Exception as e:
                log.error("Error in Mastodon campaigns bot: %s", e)
                log.exception(e)
            finally:
                self._bot_campaign_stop_event.wait(poll_interval * 3600)

    def start_campaigns_bot(self):
        if not self.__is_enabled:
            log.debug("Mastodon campaigns bot is disabled.")
            return

        if self._bot_campaign_thread and self._bot_campaign_thread.is_alive():
            log.info("Mastodon campaigns bot is already running.")
            return

        log.info("Starting Mastodon campaigns bot...")
        self._bot_campaign_stop_event.clear()
        self._bot_campaign_thread = Thread(
            target=self._campaigns_bot_main,
            name="MastodonCampaignsBotThread",
            daemon=True,
        )
        self._bot_campaign_thread.start()

    def stop_campaigns_bot(self):
        if not self._bot_campaign_thread:
            return

        log.info("Stopping Mastodon campaigns bot...")
        self._bot_campaign_stop_event.set()
        self._bot_campaign_thread.join()
        log.info("Mastodon campaigns bot stopped.")
