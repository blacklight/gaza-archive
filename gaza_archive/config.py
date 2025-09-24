import os
import logging
import sys
from dataclasses import dataclass


@dataclass
class Config:  # pylint: disable=too-few-public-methods
    """
    Main configuration class.
    """

    accounts_source_url: str
    http_timeout: int
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
            accounts_source_url=os.getenv(
                "ACCOUNTS_SOURCE_URL", "https://gaza-verified.org"
            ),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "20")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
