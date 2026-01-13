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

    @computed_field
    @property
    def string(self) -> str:
        return str(self)

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

    def __str__(self) -> str:
        """
        String representation of the amount.
        """
        display_amount = f"{self.amount:,.2f}"
        if self.currency == "USD":
            return f"${display_amount}"
        if self.currency == "EUR":
            return f"€{display_amount}"
        if self.currency == "GBP":
            return f"£{display_amount}"
        if self.currency == "JPY":
            return f"¥{display_amount}"
        if self.currency == "CNY":
            return f"¥{display_amount}"
        if self.currency == "INR":
            return f"₹{display_amount}"
        if self.currency == "AUD":
            return f"A${display_amount}"
        if self.currency == "CAD":
            return f"C${display_amount}"
        if self.currency == "CHF":
            return f"CHF {display_amount}"
        if self.currency == "SEK":
            return f"{display_amount} kr"
        if self.currency == "NZD":
            return f"NZ${display_amount}"
        if self.currency == "MXN":
            return f"${display_amount} MXN"
        if self.currency == "SGD":
            return f"S${display_amount}"
        if self.currency == "HKD":
            return f"HK${display_amount}"
        if self.currency == "NOK":
            return f"{display_amount} kr"
        if self.currency == "KRW":
            return f"₩{display_amount}"
        if self.currency == "TRY":
            return f"₺{display_amount}"
        if self.currency == "RUB":
            return f"₽{display_amount}"
        if self.currency == "BRL":
            return f"R${display_amount}"
        if self.currency == "ZAR":
            return f"R {display_amount}"
        if self.currency == "PLN":
            return f"{display_amount} zł"
        if self.currency == "DKK":
            return f"{display_amount} kr"
        if self.currency == "TWD":
            return f"NT${display_amount}"
        if self.currency == "THB":
            return f"฿{display_amount}"
        if self.currency == "MYR":
            return f"RM{display_amount}"
        if self.currency == "IDR":
            return f"Rp{display_amount}"
        if self.currency == "CZK":
            return f"{display_amount} Kč"
        if self.currency == "HUF":
            return f"{display_amount} Ft"
        if self.currency == "ILS":
            return f"₪{display_amount}"
        if self.currency == "AED":
            return f"د.إ {display_amount}"
        if self.currency == "SAR":
            return f"ر.س {display_amount}"
        if self.currency == "CLP":
            return f"${display_amount} CLP"
        if self.currency == "COP":
            return f"${display_amount} COP"
        if self.currency == "PEN":
            return f"S/ {display_amount}"
        if self.currency == "ARS":
            return f"${display_amount} ARS"
        if self.currency == "VND":
            return f"₫{display_amount}"
        if self.currency == "EGP":
            return f"ج.م {display_amount}"
        if self.currency == "PKR":
            return f"₨{display_amount}"
        if self.currency == "BDT":
            return f"৳{display_amount}"
        if self.currency == "LKR":
            return f"රු{display_amount}"
        if self.currency == "NGN":
            return f"₦{display_amount}"
        if self.currency == "GHS":
            return f"₵{display_amount}"
        if self.currency == "KES":
            return f"KSh {display_amount}"
        if self.currency == "TZS":
            return f"TSh {display_amount}"
        if self.currency == "UGX":
            return f"USh {display_amount}"
        if self.currency == "MAD":
            return f"د.م. {display_amount}"
        if self.currency == "DZD":
            return f"د.ج {display_amount}"
        if self.currency == "TND":
            return f"د.ت {display_amount}"
        if self.currency == "LYD":
            return f"ل.د {display_amount}"
        if self.currency == "BHD":
            return f".د.ب {display_amount}"
        if self.currency == "OMR":
            return f"ر.ع. {display_amount}"
        if self.currency == "JOD":
            return f"د.ا {display_amount}"
        if self.currency == "QAR":
            return f"ر.ق {display_amount}"
        if self.currency == "KWD":
            return f"د.ك {display_amount}"
        if self.currency == "BND":
            return f"B${display_amount}"
        if self.currency == "COP":
            return f"${display_amount} COP"
        if self.currency == "DOP":
            return f"RD${display_amount}"
        if self.currency == "CRC":
            return f"₡{display_amount}"
        if self.currency == "HNL":
            return f"L {display_amount}"
        if self.currency == "NIO":
            return f"C$ {display_amount}"
        if self.currency == "PAB":
            return f"B/. {display_amount}"
        if self.currency == "SVC":
            return f"$ {display_amount} SVC"
        if self.currency == "JMD":
            return f"J$ {display_amount}"
        if self.currency == "BBD":
            return f"Bds$ {display_amount}"
        if self.currency == "TTD":
            return f"TT$ {display_amount}"

        return f"{display_amount} {self.currency}"


class CampaignStats(BaseModel):
    """
    Model for campaign stats records.
    """

    group_key: list[str] = Field(default_factory=list)
    group_value: list[str | None] = Field(default_factory=list)
    data: list["CampaignStats"] | list["CampaignAccountStats"] = Field(
        default_factory=list
    )
    _amount: CampaignStatsAmount | None = None
    _first_donation_time: datetime | None = None
    _last_donation_time: datetime | None = None
    _last_activity_time: datetime | None = None

    def __init__(
        self,
        amount: CampaignStatsAmount | None = None,
        first_donation_time: datetime | None = None,
        last_donation_time: datetime | None = None,
        last_activity_time: datetime | None = None,
        **data,
    ):
        super().__init__(**data)
        if amount is not None:
            self._amount = amount
        if first_donation_time is not None:
            self._first_donation_time = first_donation_time
        if last_donation_time is not None:
            self._last_donation_time = last_donation_time
        if last_activity_time is not None:
            self._last_activity_time = last_activity_time

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

    @computed_field
    @property
    def last_activity_time(self) -> datetime | None:
        if self._last_activity_time:
            return self._last_activity_time
        times = [
            group.last_activity_time
            for group in self.data
            if group.last_activity_time is not None
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
