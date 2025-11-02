from datetime import datetime
from enum import Enum

from pydantic import Field, computed_field

from ._base import Item


class CampaignType(Enum):
    """
    Enumeration of campaign types.
    """

    GFM = "gfm"
    CHUFFED = "chuffed"


class CampaignDonation(Item):
    """
    Campaign donation object.
    """

    id: str
    campaign_url: str
    amount: float  # Always in USD
    created_at: datetime
    donor: str | None = None


class Campaign(Item):
    """
    Campaign object.
    """

    account_url: str
    donations_cursor: str | None = None
    donations: list[CampaignDonation] = Field(default_factory=list)

    @computed_field
    @property
    def type(self) -> CampaignType:
        if "gofundme.com" in self.url:
            return CampaignType.GFM
        if "chuffed.org" in self.url:
            return CampaignType.CHUFFED
        raise ValueError(f"Unsupported campaign URL: {self.url}")
