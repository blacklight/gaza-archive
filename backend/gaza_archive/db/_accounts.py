from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..model import Account
from ._model import Account as DbAccount, Post as DbPost

log = getLogger(__name__)


class Accounts(ABC):
    """
    Database interface for accounts.
    """

    _write_lock: RLock

    def __init__(self, *_, **__):
        self._accounts: dict[str, Account] = {}

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def _load_accounts(self) -> dict[str, Account]:
        log.debug("Loading accounts from database...")
        self._accounts = self.get_accounts()
        log.info("Loaded %d accounts from database.", len(self._accounts))
        return self._accounts

    def get_accounts(
        self, limit: int | None = None, offset: int | None = None
    ) -> dict[str, Account]:
        with self.get_session() as session:
            latest_post_subquery = (
                session.query(
                    DbPost.author_url, func.max(DbPost.id).label("last_status_id")
                )
                .group_by(DbPost.author_url)
                .subquery()
            )

            db_accounts = (
                session.query(DbAccount, latest_post_subquery.c.last_status_id)
                .outerjoin(
                    latest_post_subquery,
                    DbAccount.url == latest_post_subquery.c.author_url,
                )
                .order_by(DbAccount.url)
                .limit(limit if limit is not None else None)
                .offset(offset if offset is not None else 0)
                .all()
            )

            return {
                str(db_account.url): db_account.to_model(last_status_id=last_status_id)
                for db_account, last_status_id in db_accounts
            }

    def get_account(self, account_url: str) -> Account | None:
        with self.get_session() as session:
            latest_post_subquery = (
                session.query(
                    DbPost.author_url, func.max(DbPost.id).label("last_status_id")
                )
                .group_by(DbPost.author_url)
                .subquery()
            )

            result = (
                session.query(DbAccount, latest_post_subquery.c.last_status_id)
                .outerjoin(
                    latest_post_subquery,
                    DbAccount.url == latest_post_subquery.c.author_url,
                )
                .filter(DbAccount.url == account_url)
                .first()
            )

            if result:
                db_account, last_status_id = result
                return db_account.to_model(last_status_id=last_status_id)
            return None

    def save_accounts(self, accounts: list[Account]):
        accounts_by_url = {account.url: account for account in accounts}

        with self._write_lock, self.get_session() as session:
            db_accounts: dict[str, DbAccount] = {
                str(db_account.url): db_account
                for db_account in (
                    session.query(DbAccount)
                    .filter(DbAccount.url.in_(accounts_by_url.keys()))
                    .all()
                )
            }

            for account in accounts:
                db_account = db_accounts.get(account.url)
                if db_account and account != db_account.to_model():
                    log.info("Updating account: %s", account.url)
                    db_account.update_from_model(account)
                    session.merge(db_account)
                elif not db_account:
                    log.info("Adding new account: %s", account.url)
                    session.add(DbAccount.from_model(account))

            session.commit()
