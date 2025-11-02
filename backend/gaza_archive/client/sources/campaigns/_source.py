import re
from abc import ABC, abstractmethod

from ....config import Config
from ....db import Db
from ....model import Campaign


class CampaignSource(ABC):
    """
    Base class for campaign sources.
    """

    def __init__(self, config: Config, db: Db, *_, **__):
        self.config = config
        self.db = db

    @property
    @abstractmethod
    def url_pattern(self) -> re.Pattern:
        """
        Returns the regex pattern to identify the source from a URL.
        """

    def accepts_url(self, url: str) -> bool:
        """
        Check if the source accepts the given URL.
        """
        return bool(self.url_pattern.match(url))

    def parse_url(self, url: str) -> str | None:
        """
        Parse the campaign URL from the given URL.
        """
        return url

    @abstractmethod
    def fetch_donations(self, campaign: Campaign) -> Campaign:
        """
        Fetch donations from the campaign URL.
        """
