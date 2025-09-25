from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..model import Account as ModelAccount, Media as ModelMedia, Post as ModelPost

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
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author")

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
            profile_note=model.profile_note,
            created_at=model.created_at,
        )

    def to_model(self, last_status_id: str | None = None) -> ModelAccount:
        return ModelAccount(
            url=self.url,  # type: ignore
            id=self.id,  # type: ignore
            display_name=self.display_name,  # type: ignore
            avatar_url=self.avatar_url,  # type: ignore
            header_url=self.header_url,  # type: ignore
            profile_note=self.profile_note,  # type: ignore
            created_at=self.created_at,  # type: ignore
            last_status_id=last_status_id,
        )

    def update_from_model(self, model: ModelAccount):
        self.display_name = model.display_name
        self.avatar_url = model.avatar_url
        self.header_url = model.header_url
        self.profile_note = model.profile_note
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
            author_url=model.author_url,
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
            author_url=self.author_url,  # type: ignore
            content=self.content,  # type: ignore
            in_reply_to_id=self.in_reply_to_id,  # type: ignore
            in_reply_to_account_id=self.in_reply_to_account_id,  # type: ignore
            quote=self.quote,  # type: ignore
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,  # type: ignore
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
    def from_model(cls, model: ModelMedia, post_url: str) -> "Media":
        return cls(
            url=model.url,
            id=model.id,
            type=model.type,
            description=model.description,
            post_url=post_url,
        )

    def to_model(self, post_url: str | None = None) -> ModelMedia:
        return ModelMedia(
            url=self.url,  # type: ignore
            id=self.id,  # type: ignore
            type=self.type,  # type: ignore
            description=self.description,  # type: ignore
            post_url=post_url or self.post_url,  # type: ignore
        )
