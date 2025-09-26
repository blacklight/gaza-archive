import os
import logging
import sys
from dataclasses import dataclass


@dataclass
class Config:  # pylint: disable=too-few-public-methods
    """
    Main configuration class.
    """

    storage_path: str
    accounts_source_url: str
    http_timeout: int
    poll_interval: int
    db_url: str
    user_agent: str
    concurrent_requests: int
    download_media: bool
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
            storage_path=os.getenv("STORAGE_PATH", "./data"),
            accounts_source_url=os.getenv(
                "ACCOUNTS_SOURCE_URL", "https://gaza-verified.org"
            ),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "20")),
            poll_interval=int(os.getenv("POLL_INTERVAL", "300")),
            db_url=os.getenv("DB_URL", "sqlite:///./data.db"),
            user_agent=os.getenv("USER_AGENT", "GazaVerifiedArchiveBot/1.0"),
            concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "5")),
            download_media=(
                os.getenv("DOWNLOAD_MEDIA", "true").lower() in ("true", "1", "yes")
            ),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        )
