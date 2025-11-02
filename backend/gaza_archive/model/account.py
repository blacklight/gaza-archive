from datetime import datetime

from pydantic import Field, computed_field

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
    profile_fields: dict[str, str] = Field(default_factory=dict)
    disabled: bool = False
    campaign_url: str | None = None
    last_status_id: str | None = None
    created_at: datetime | None = None

    @computed_field
    @property
    def username(self) -> str:
        return self.url.split("/")[-1].lstrip("@")

    @computed_field
    @property
    def feed_url(self) -> str:
        return f"{self.url}.rss"

    @computed_field
    @property
    def instance(self) -> str:
        return self.url.split("/")[2]

    @computed_field
    @property
    def instance_url(self) -> str:
        return f"https://{self.instance}"

    @property
    def instance_api_url(self) -> str:
        return f"https://{self.instance}/api/v1"

    @computed_field
    @property
    def fqn(self) -> str:
        return f"@{self.username}@{self.instance}"

    @computed_field
    @property
    def api_url(self) -> str:
        assert self.id, "Account ID is not set"
        return f"{self.instance_api_url}/accounts/{self.id}"

    @computed_field
    @property
    def avatar_path(self) -> str | None:
        if not self.avatar_url:
            return None
        return f"/media/{self.fqn}/avatars/{self.avatar_url.split('/')[-1]}"

    @computed_field
    @property
    def header_path(self) -> str | None:
        if not self.header_url:
            return None
        return f"/media/{self.fqn}/headers/{self.header_url.split('/')[-1]}"

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
            and self.profile_fields == other.profile_fields
            and self.campaign_url == other.campaign_url
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
        self.profile_fields = dict(other.profile_fields)
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
