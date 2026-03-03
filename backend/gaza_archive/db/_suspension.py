from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timezone
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model.suspension import (
    AccountSuspensionState,
    AccountSuspensionStateAudit,
    SuspensionState,
)
from ._model import (
    AccountSuspensionState as DbAccountSuspensionState,
    AccountSuspensionStateAudit as DbAccountSuspensionStateAudit,
)

log = getLogger(__name__)


class SuspensionStates(ABC):
    """
    Database interface for account suspension states.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def get_suspension_states(self, account_url: str) -> dict[str, SuspensionState]:
        """Get all suspension states for an account across servers."""
        with self.get_session() as session:
            states = (
                session.query(DbAccountSuspensionState)
                .filter(DbAccountSuspensionState.account_url == account_url)
                .all()
            )

            return {
                str(state.server_url): SuspensionState(state.state) for state in states
            }

    def get_account_state_on_instance(
        self, account_url: str, server_url: str
    ) -> SuspensionState | None:
        """Get suspension state for a specific account on a specific server."""
        with self.get_session() as session:
            state = (
                session.query(DbAccountSuspensionState)
                .filter(
                    DbAccountSuspensionState.account_url == account_url,
                    DbAccountSuspensionState.server_url == server_url,
                )
                .first()
            )

            return SuspensionState(state.state) if state else None

    def save_suspension_states(
        self,
        account_url: str,
        states: dict[str, SuspensionState],
        create_audit: bool = True,
    ):
        """Save suspension states for an account, creating audit records for changes."""

        with self._write_lock, self.get_session() as session:
            # Get existing states for audit comparison
            existing_states = {}
            if create_audit:
                existing_db_states = (
                    session.query(DbAccountSuspensionState)
                    .filter(DbAccountSuspensionState.account_url == account_url)
                    .all()
                )
                existing_states = {
                    str(s.server_url): s.state for s in existing_db_states
                }

            # Delete existing states for this account
            session.query(DbAccountSuspensionState).filter(
                DbAccountSuspensionState.account_url == account_url
            ).delete(synchronize_session=False)

            # Insert new states
            for server_url, state in states.items():
                db_state = DbAccountSuspensionState(
                    account_url=account_url,
                    server_url=server_url,
                    state=state,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(db_state)

                # Create audit record if state changed
                if create_audit:
                    old_state = existing_states.get(server_url)
                    if old_state != state:  # type: ignore
                        audit = DbAccountSuspensionStateAudit(
                            account_url=account_url,
                            server_url=server_url,
                            old_state=old_state,
                            new_state=state,
                            changed_at=datetime.now(timezone.utc),
                        )
                        session.add(audit)

            session.commit()

    def get_accounts_needing_state_refresh(self) -> list[str]:
        """Get accounts that need state refresh (those from verified source)."""
        # This will be called from the background job with accounts from
        # https://gaza-verified.org/people.json
        # For now, return empty list - implementation in Phase 6
        return []

    def get_account_suspension_states(
        self,
        account_url: str,
        states: list[SuspensionState] | None = None,
        servers: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AccountSuspensionState]:
        """Get suspension states for an account with filtering support for API."""
        with self.get_session() as session:
            query = session.query(DbAccountSuspensionState).filter(
                DbAccountSuspensionState.account_url == account_url
            )

            if states:
                query = query.filter(DbAccountSuspensionState.state.in_(states))

            if servers:
                query = query.filter(DbAccountSuspensionState.server_url.in_(servers))

            # Order by server_url for consistent pagination (before limit/offset)
            query = query.order_by(DbAccountSuspensionState.server_url)

            if offset:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            return [state.to_model() for state in query.all()]

    def get_account_suspension_audit(
        self,
        account_url: str,
        states: list[SuspensionState] | None = None,
        servers: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AccountSuspensionStateAudit]:
        """Get suspension state audit trail for an account with filtering support for API."""
        with self.get_session() as session:
            query = session.query(DbAccountSuspensionStateAudit).filter(
                DbAccountSuspensionStateAudit.account_url == account_url
            )

            if states:
                # Filter by either old_state or new_state matching any of the requested states
                query = query.filter(
                    (DbAccountSuspensionStateAudit.old_state.in_(states))
                    | (DbAccountSuspensionStateAudit.new_state.in_(states))
                )

            if servers:
                query = query.filter(
                    DbAccountSuspensionStateAudit.server_url.in_(servers)
                )

            if start_time:
                query = query.filter(
                    DbAccountSuspensionStateAudit.changed_at >= start_time
                )

            if end_time:
                query = query.filter(
                    DbAccountSuspensionStateAudit.changed_at <= end_time
                )

            # Order by changed_at descending (most recent first) for audit trail (before limit/offset)
            query = query.order_by(DbAccountSuspensionStateAudit.changed_at.desc())

            if offset:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            return [audit.to_model() for audit in query.all()]
