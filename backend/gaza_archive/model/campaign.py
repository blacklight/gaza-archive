from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_serializer

from ._base import Item
from .account import Account


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


class CampaignStatsAmount(BaseModel):
    """
    Model for amount objects in campaign stats.
    """

    amount: float
    currency: str = "USD"

    @field_serializer("amount")
    def serialize_amount(self, value: float) -> float:
        """Round amount to 2 decimal places for serialization"""
        return round(value, 2)

    def __add__(self, other) -> "CampaignStatsAmount":
        """
        Adds two CampaignStatsAmount objects.
        """
        if self.amount == 0.0:
            return other
        if other.amount == 0.0:
            return self
        if self.currency != other.currency:
            raise ValueError("Cannot add amounts with different currencies")

        return CampaignStatsAmount(
            amount=self.amount + other.amount,
            currency=self.currency,
        )


class CampaignStats(BaseModel):
    """
    Model for campaign stats records.
    """

    group_key: list[str] = Field(default_factory=list)
    group_value: list[str | None] = Field(default_factory=list)
    data: list["CampaignStats"] = Field(default_factory=list)
    _amount: CampaignStatsAmount | None = None
    _first_donation_time: datetime | None = None
    _last_donation_time: datetime | None = None

    def __init__(
        self,
        amount: CampaignStatsAmount | None = None,
        first_donation_time: datetime | None = None,
        last_donation_time: datetime | None = None,
        **data,
    ):
        super().__init__(**data)
        if amount is not None:
            self._amount = amount
        if first_donation_time is not None:
            self._first_donation_time = first_donation_time
        if last_donation_time is not None:
            self._last_donation_time = last_donation_time

    @computed_field
    @property
    def amount(self) -> CampaignStatsAmount:
        """
        Total amount for this record.
        """
        return self._amount or sum(
            (group.amount for group in self.data),
            CampaignStatsAmount(amount=0.0),
        )

    @computed_field
    @property
    def first_donation_time(self) -> datetime | None:
        """
        Earliest donation time for this record.
        """
        if self._first_donation_time:
            return self._first_donation_time
        times = [
            group.first_donation_time
            for group in self.data
            if group.first_donation_time is not None
        ]
        return min(times) if times else None

    @computed_field
    @property
    def last_donation_time(self) -> datetime | None:
        """
        Latest donation time for this record.
        """
        if self._last_donation_time:
            return self._last_donation_time
        times = [
            group.last_donation_time
            for group in self.data
            if group.last_donation_time is not None
        ]
        return max(times) if times else None


class CampaignAccountStats(CampaignStats):
    """
    Account campaign stats model.
    """

    account: Account


class CampaignDonationInfo(BaseModel):
    """
    Model for a campaign donation response item.
    """

    id: str
    account: Account
    campaign_url: str
    amount: CampaignStatsAmount
    donor: str | None = None
    created_at: datetime
