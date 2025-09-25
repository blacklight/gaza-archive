from dataclasses import dataclass
from datetime import datetime

from ._base import Item


@dataclass
class Account(Item):
    """
    Account class representing user account information.
    """

    id: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    header_url: str | None = None
    profile_note: str | None = None
    disabled: bool = False
    created_at: datetime | None = None
    last_updated_at: datetime | None = None

    # TODO Add followers, following, posts, profile fields etc.

    @property
    def username(self) -> str:
        return self.url.split("/")[-1].lstrip("@")

    @property
    def feedURL(self) -> str:
        return f"{self.url}.rss"

    @property
    def instance(self) -> str:
        return self.url.split("/")[2]

    @property
    def instanceURL(self) -> str:
        return f"https://{self.instance}"

    @property
    def instanceApiUrl(self) -> str:
        return f"https://{self.instance}/api/v1"

    @property
    def apiURL(self) -> str:
        assert self.id, "Account ID is not set"
        return f"{self.instanceApiUrl}/accounts/{self.id}"

    def __eq__(self, other) -> bool:
        """
        Compare two Account instances for equality.
        """
        if not isinstance(other, Account):
            return False

        return (
            self.url == other.url
            and self.id == other.id
            and self.display_name == other.display_name
            and self.avatar_url == other.avatar_url
            and self.header_url == other.header_url
            and self.profile_note == other.profile_note
            and self.disabled == other.disabled
            and (
                (self.created_at is None and other.created_at is None)
                or self.created_at == other.created_at
            )
            and (
                (self.last_updated_at is None and other.last_updated_at is None)
                or self.last_updated_at == other.last_updated_at
            )
        )

    def merge(self, other: "Account") -> "Account":
        """
        Merge another Account instance into this one.
        """
        assert isinstance(other, Account)

        self.id = other.id
        self.display_name = other.display_name
        self.avatar_url = other.avatar_url
        self.header_url = other.header_url
        self.profile_note = other.profile_note
        self.disabled = other.disabled
        if other.created_at:
            self.created_at = other.created_at
        if other.last_updated_at:
            self.last_updated_at = other.last_updated_at

        return self
