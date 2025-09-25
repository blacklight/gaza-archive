from contextlib import contextmanager
from logging import getLogger
from threading import RLock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ..model import Account
from ._model import Base, Account as DbAccount

log = getLogger(__name__)


class Db:
    """
    Database class for managing the database connection and sessions.
    """

    def __init__(self, config: Config):
        self.config = config
        self.engine = create_engine(self.config.db_url, echo=self.config.debug)
        self.Session = sessionmaker(bind=self.engine)
        self._accounts: dict[str, Account] = {}
        self._write_lock = RLock()

        Base.metadata.create_all(self.engine)
        self._load_accounts()

    @contextmanager
    def get_session(self):
        with self.Session() as session:
            yield session

    def _load_accounts(self) -> dict[str, Account]:
        log.debug("Loading accounts from database...")
        with self.get_session() as session:
            db_accounts = session.query(DbAccount).all()
            self._accounts = {
                str(db_account.url): db_account.to_model() for db_account in db_accounts
            }

        log.info("Loaded %d accounts from database.", len(self._accounts))
        return self._accounts

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
