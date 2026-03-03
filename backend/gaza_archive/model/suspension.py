from enum import Enum
from datetime import datetime

from ._base import Item


class SuspensionState(Enum):
    """
    Account suspension states on Mastodon instances.
    """

    ACTIVE = "ACTIVE"
    LIMITED = "LIMITED"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class AccountSuspensionState(Item):
    """
    Account suspension state on a specific server.
    """

    account_url: str
    server_url: str
    state: SuspensionState
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AccountSuspensionStateAudit(Item):
    """
    Audit record for account suspension state changes.
    """

    id: int | None = None
    account_url: str
    server_url: str
    old_state: SuspensionState | None = None
    new_state: SuspensionState
    changed_at: datetime | None = None
