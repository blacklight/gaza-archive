from contextlib import contextmanager
from logging import getLogger
from threading import RLock

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ..model import Account, Post
from ._model import Base, Account as DbAccount, Media as DbMedia, Post as DbPost

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
                .all()
            )

            self._accounts = {
                str(db_account.url): db_account.to_model(last_status_id=last_status_id)
                for db_account, last_status_id in db_accounts
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

    def save_posts(self, posts: list[Post]):
        with self._write_lock, self.get_session() as session:
            db_posts: dict[str, DbPost] = {
                str(db_post.url): db_post
                for db_post in (
                    session.query(DbPost)
                    .filter(DbPost.url.in_([post.url for post in posts]))
                    .all()
                )
            }

            for post in posts:
                if post.url not in db_posts:
                    log.info(
                        "Adding new post with %d attachments: %s",
                        len(post.attachments),
                        post.url,
                    )
                    session.add(DbPost.from_model(post))

                    for media in post.attachments:
                        session.add(DbMedia.from_model(media))

            session.commit()
