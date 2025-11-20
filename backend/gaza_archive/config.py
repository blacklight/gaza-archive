import os
import logging
import re
import sys
from dataclasses import dataclass


@dataclass
class Config:  # pylint: disable=too-few-public-methods
    """
    Main configuration class.
    """

    base_url: str
    storage_path: str
    accounts_source_url: str
    http_timeout: int
    poll_interval: int
    db_url: str
    api_host: str
    api_port: int
    user_agent: str
    concurrent_requests: int
    download_media: bool
    enable_crawlers: bool
    enable_campaign_crawlers: bool
    campaign_url_http_proxy: str | None
    exchange_rates_api_key: str | None
    fixer_io_api_key: str | None
    exclude_profiles: list[str]
    exclude_campaign_accounts: list[str]
    hide_donors: bool
    mastodon_accounts_bot_instance_url: str
    mastodon_accounts_bot_access_token: str
    mastodon_campaigns_bot_instance_url: str
    mastodon_campaigns_bot_access_token: str
    mastodon_campaigns_bot_time_window_days: int
    mastodon_campaigns_bot_min_raise_amount: float
    mastodon_campaigns_bot_post_interval_hours: float
    debug: bool

    def __post_init__(self):
        """
        Post-initialization to set up logging.
        """
        logging.basicConfig(
            stream=sys.stdout, level=logging.INFO if not self.debug else logging.DEBUG
        )

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create a Config instance from environment variables.
        """
        base_url = os.getenv("BASE_URL", "http://localhost:8000")

        return cls(
            base_url=base_url,
            storage_path=os.getenv("STORAGE_PATH", "./data"),
            accounts_source_url=os.getenv(
                "ACCOUNTS_SOURCE_URL", "https://gaza-verified.org/people.json"
            ),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "20")),
            poll_interval=int(os.getenv("POLL_INTERVAL", "300")),
            db_url=os.getenv("DB_URL", "sqlite:///./data.db"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            user_agent=(
                os.getenv("USER_AGENT", "GazaVerifiedArchiveBot/1.0")
                + f" (+{base_url})"
            ),
            concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "5")),
            download_media=(
                os.getenv("DOWNLOAD_MEDIA", "true").lower() in ("true", "1", "yes")
            ),
            enable_crawlers=(
                os.getenv("ENABLE_CRAWLERS", "true").lower() in ("true", "1", "yes")
            ),
            enable_campaign_crawlers=(
                os.getenv("ENABLE_CAMPAIGN_CRAWLERS", "true").lower()
                in ("true", "1", "yes")
            ),
            campaign_url_http_proxy=os.getenv("CAMPAIGN_URL_HTTP_PROXY"),
            exchange_rates_api_key=os.getenv("EXCHANGE_RATES_API_KEY"),
            fixer_io_api_key=os.getenv("FIXER_IO_API_KEY"),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            exclude_profiles=list(
                {
                    profile
                    for profile in re.split(
                        r"\s*,\s*",
                        os.getenv("EXCLUDE_PROFILES", "").strip(),
                    )
                    if profile
                }
            ),
            exclude_campaign_accounts=list(
                {
                    account
                    for account in re.split(
                        r"\s*,\s*",
                        os.getenv("EXCLUDE_CAMPAIGN_ACCOUNTS", "").strip(),
                    )
                    if account
                }
            ),
            mastodon_accounts_bot_instance_url=os.getenv(
                "MASTODON_ACCOUNTS_BOT_INSTANCE_URL", ""
            ),
            mastodon_accounts_bot_access_token=os.getenv(
                "MASTODON_ACCOUNTS_BOT_ACCESS_TOKEN", ""
            ),
            mastodon_campaigns_bot_instance_url=os.getenv(
                "MASTODON_CAMPAIGNS_BOT_INSTANCE_URL", ""
            ),
            mastodon_campaigns_bot_access_token=os.getenv(
                "MASTODON_CAMPAIGNS_BOT_ACCESS_TOKEN", ""
            ),
            mastodon_campaigns_bot_time_window_days=int(
                os.getenv("MASTODON_CAMPAIGNS_BOT_TIME_WINDOW_DAYS", "7")
            ),
            mastodon_campaigns_bot_min_raise_amount=float(
                os.getenv("MASTODON_CAMPAIGNS_BOT_MIN_RAISE_AMOUNT", "200.0")
            ),
            mastodon_campaigns_bot_post_interval_hours=float(
                os.getenv("MASTODON_CAMPAIGNS_BOT_POST_INTERVAL_HOURS", "6.0")
            ),
            hide_donors=(
                os.getenv("HIDE_DONORS", "false").lower() in ("true", "1", "yes")
            ),
        )
