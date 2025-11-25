import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..model import (
    Account as ModelAccount,
    BotState as ModelBotState,
    Campaign as ModelCampaign,
    CampaignDonation as ModelCampaignDonation,
    Media as ModelMedia,
    Post as ModelPost,
)

Base = declarative_base()

# Association table for Follower many-to-many relationship
follower_association = Table(
    "followers",
    Base.metadata,
    Column("account_url", String, ForeignKey("accounts.url"), primary_key=True),
    Column("followed_url", String, ForeignKey("accounts.url"), primary_key=True),
)


def utcnow():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    url = Column(String, primary_key=True)
    id = Column(String, nullable=False, index=True)
    display_name = Column(String)
    avatar_url = Column(String)
    header_url = Column(String)
    profile_note = Column(Text)
    profile_fields = Column(JSON)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    campaign_url = Column(String, ForeignKey("campaigns.url"), unique=True)

    # Relationships
    posts = relationship("Post", back_populates="author")
    campaign = relationship("Campaign", back_populates="account", uselist=False)

    # Self-referential many-to-many for followers
    following = relationship(
        "Account",
        secondary=follower_association,
        primaryjoin=url == follower_association.c.account_url,
        secondaryjoin=url == follower_association.c.followed_url,
        back_populates="followers",
    )

    followers = relationship(
        "Account",
        secondary=follower_association,
        primaryjoin=url == follower_association.c.followed_url,
        secondaryjoin=url == follower_association.c.account_url,
        back_populates="following",
    )

    @classmethod
    def from_model(cls, model: ModelAccount) -> "Account":
        return cls(
            url=model.url,
            id=model.id,
            display_name=model.display_name,
            avatar_url=model.avatar_url,
            header_url=model.header_url,
            campaign_url=model.campaign_url,
            profile_note=model.profile_note,
            profile_fields=model.profile_fields,
            created_at=model.created_at,
        )

    def to_model(self, last_status_id: str | None = None) -> ModelAccount:
        return ModelAccount(
            url=self.url,  # type: ignore
            id=self.id,  # type: ignore
            display_name=self.display_name,  # type: ignore
            avatar_url=self.avatar_url,  # type: ignore
            header_url=self.header_url,  # type: ignore
            campaign_url=self.campaign_url,  # type: ignore
            profile_note=self.profile_note,  # type: ignore
            profile_fields=self.profile_fields or {},  # type: ignore
            created_at=self.created_at,  # type: ignore
            last_status_id=last_status_id,
            disabled=False,
        )

    def update_from_model(self, model: ModelAccount):
        self.display_name = model.display_name
        self.avatar_url = model.avatar_url
        self.header_url = model.header_url
        self.campaign_url = (
            model.campaign_url if model.campaign_url else self.campaign_url
        )
        self.profile_note = model.profile_note
        self.profile_fields = model.profile_fields
        self.disabled = model.disabled
        self.created_at = model.created_at


class Post(Base):
    __tablename__ = "posts"

    url = Column(String, primary_key=True)
    id = Column(String, nullable=False, index=True)
    author_url = Column(
        String,
        ForeignKey("accounts.url", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text)
    in_reply_to_id = Column(String)
    in_reply_to_account_id = Column(String)
    quote = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    author = relationship("Account", back_populates="posts")
    media = relationship("Media", back_populates="post")

    @classmethod
    def from_model(cls, model: ModelPost) -> "Post":
        return cls(
            url=model.url,
            id=model.id,
            author_url=model.author.url,
            content=model.content,
            in_reply_to_id=model.in_reply_to_id,
            in_reply_to_account_id=model.in_reply_to_account_id,
            quote=model.quote,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self) -> ModelPost:
        return ModelPost(
            url=self.url,  # type: ignore
            id=self.id,  # type: ignore
            author=self.author.to_model() if self.author else None,  # type: ignore
            content=self.content,  # type: ignore
            in_reply_to_id=self.in_reply_to_id,  # type: ignore
            in_reply_to_account_id=self.in_reply_to_account_id,  # type: ignore
            quote=self.quote,  # type: ignore
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,   # type: ignore
            attachments=[],
        )


class Media(Base):
    __tablename__ = "media"

    url = Column(String, primary_key=True)
    id = Column(String, nullable=False, index=True)
    type = Column(String)
    description = Column(Text)
    post_url = Column(
        String,
        ForeignKey("posts.url", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    post = relationship("Post", back_populates="media")

    @classmethod
    def from_model(cls, model: ModelMedia) -> "Media":
        return cls(
            url=model.url,
            id=model.id,
            type=model.type,
            description=model.description,
            post_url=model.post.url if model.post else None,
        )

    def to_model(self) -> ModelMedia:
        return ModelMedia(
            url=self.url,  # type: ignore
            id=self.id,  # type: ignore
            type=self.type,  # type: ignore
            description=self.description,  # type: ignore
            post=self.post.to_model() if self.post else None,  # type: ignore
        )


class ExchangeRate(Base):
    """SQLAlchemy model for exchange rates cache."""

    __tablename__ = "exchange_rates"

    date = Column(String, nullable=False, primary_key=True)
    rates_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __init__(self, date: str, rates: dict):
        self.date = date
        self.rates_json = json.dumps(rates)

    @property
    def rates(self) -> dict:
        """Get rates as dictionary."""
        return json.loads(str(self.rates_json))

    @rates.setter
    def rates(self, value: dict):
        """Set rates from dictionary."""
        self.rates_json = json.dumps(value)
        self.updated_at = utcnow()

    def __repr__(self):
        """String representation of ExchangeRate."""
        return f"<ExchangeRate(date='{self.date}', rates_count={len(self.rates)})>"


class Campaign(Base):
    """SQLAlchemy model for fundraising campaigns."""

    __tablename__ = "campaigns"

    url = Column(String, primary_key=True)
    donations_cursor = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    account = relationship("Account", back_populates="campaign")
    donations = relationship("CampaignDonation", back_populates="campaign")

    @classmethod
    def from_model(cls, model: "ModelCampaign") -> "Campaign":
        return cls(
            url=model.url,
            donations_cursor=model.donations_cursor,
        )

    def to_model(self) -> ModelCampaign:
        donations = [donation.to_model() for donation in self.donations]
        return ModelCampaign(
            url=self.url,  # type: ignore
            account_url=self.account[0].url,  # type: ignore
            donations_cursor=self.donations_cursor,  # type: ignore
            donations=donations,
        )


class CampaignDonation(Base):
    """SQLAlchemy model for donations to campaigns."""

    __tablename__ = "campaign_donations"

    id = Column(String, primary_key=True)
    campaign_url = Column(
        String,
        ForeignKey("campaigns.url", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    donor = Column(String, index=True)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="donations")

    @classmethod
    def from_model(cls, model: "ModelCampaignDonation") -> "CampaignDonation":
        return cls(
            id=model.id,
            campaign_url=model.campaign_url,
            donor=model.donor,
            amount=model.amount,
            created_at=model.created_at,
        )

    def to_model(self) -> "ModelCampaignDonation":
        return ModelCampaignDonation(
            id=self.id,  # type: ignore
            url=f"{self.campaign_url}#donation-{self.id}",  # type: ignore
            campaign_url=self.campaign_url,  # type: ignore
            donor=self.donor,  # type: ignore
            amount=self.amount,  # type: ignore
            created_at=self.created_at,  # type: ignore
        )


class BotState(Base):
    """
    SQLAlchemy model for storing the state of a bot.
    """

    __tablename__ = "bot_state"

    bot_name = Column(String, primary_key=True)
    last_updated_at = Column(DateTime, default=utcnow, index=True)

    def to_model(self) -> ModelBotState:
        return ModelBotState(
            bot_name=self.bot_name,  # type: ignore
            last_updated_at=self.last_updated_at,  # type: ignore
        )