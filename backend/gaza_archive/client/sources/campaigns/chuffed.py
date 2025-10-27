import re

from ._source import CampaignSource


class ChuffedCampaignSource(CampaignSource):  # pylint: disable=too-few-public-methods
    """
    Configuration for Chuffed campaigns.
    """

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://chuffed.org/")
