import re
from abc import ABC, abstractmethod


class CampaignSource(ABC):  # pylint: disable=too-few-public-methods
    """
    Base class for campaign sources.
    """

    @property
    @abstractmethod
    def url_pattern(self) -> re.Pattern:
        """
        Returns the regex pattern to identify the source from a URL.
        """
