import re

from ._source import CampaignSource


class GFMCampaignSource(CampaignSource):  # pylint: disable=too-few-public-methods
    """
    Configuration for GoFundMe campaigns.
    """

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://gofund.me/")
