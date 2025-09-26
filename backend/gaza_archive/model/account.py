# from dataclasses import dataclass
from datetime import datetime

from pydantic import computed_field

from ._base import Item


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
    last_status_id: str | None = None
    created_at: datetime | None = None

    @computed_field
    @property
    def username(self) -> str:
        return self.url.split("/")[-1].lstrip("@")

    @computed_field
    @property
    def feedURL(self) -> str:
        return f"{self.url}.rss"

    @computed_field
    @property
    def instance(self) -> str:
        return self.url.split("/")[2]

    @computed_field
    @property
    def instanceURL(self) -> str:
        return f"https://{self.instance}"

    @property
    def instanceApiUrl(self) -> str:
        return f"https://{self.instance}/api/v1"

    @computed_field
    @property
    def fqn(self) -> str:
        return f"@{self.username}@{self.instance}"

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

        return self

    @staticmethod
    def to_url(fqn: str) -> str:
        """
        Convert a FQN to a URL.

        :param fqn: FQN in the format `@username@instance`.
        :return: URL in the format `https://instance/@username`.
        """
        if fqn.startswith("http://") or fqn.startswith("https://"):
            return fqn  # Already a URL

        if not fqn.startswith("@"):
            raise ValueError("FQN must start with '@'")

        fqn = fqn.lstrip("@")
        if "@" not in fqn:
            raise ValueError("FQN must be in the format '@username@instance'")

        username, instance = fqn.split("@", 1)
        return f"https://{instance}/@{username}"
