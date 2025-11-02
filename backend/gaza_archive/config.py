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
        return cls(
            base_url=os.getenv("BASE_URL", "http://localhost:8000"),
            storage_path=os.getenv("STORAGE_PATH", "./data"),
            accounts_source_url=os.getenv(
                "ACCOUNTS_SOURCE_URL", "https://gaza-verified.org"
            ),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "20")),
            poll_interval=int(os.getenv("POLL_INTERVAL", "300")),
            db_url=os.getenv("DB_URL", "sqlite:///./data.db"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            user_agent=os.getenv("USER_AGENT", "GazaVerifiedArchiveBot/1.0"),
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
            exclude_profiles=list({
                profile for profile in re.split(
                    r"\s*,\s*",
                    os.getenv("EXCLUDE_PROFILES", "").strip(),
                )
                if profile
            })
        )
