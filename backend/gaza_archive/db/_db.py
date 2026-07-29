from contextlib import contextmanager
from logging import getLogger
from threading import RLock

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ._bots import Bots
from ._campaigns import Campaigns
from ._currency import CurrencyConverter
from ._accounts import Accounts
from ._media import Media
from ._model import Base
from ._posts import Posts
from ._suspension import SuspensionStates

log = getLogger(__name__)


class Db(CurrencyConverter, Accounts, Campaigns, Media, Posts, Bots, SuspensionStates):
    """
    Database class for managing the database connection and sessions.
    """

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.engine = create_engine(self.config.db_url, echo=self.config.debug)
        self.Session = sessionmaker(bind=self.engine)
        self._write_lock = RLock()

        Base.metadata.create_all(self.engine)
        self._migrate()
        self._load_accounts()

    def _migrate(self):
        """
        Apply lightweight schema migrations for existing databases.

        SQLAlchemy's create_all() only creates missing tables; it does not add
        columns or alter constraints on existing tables. This method brings old
        databases in line with the current ORM definitions.
        """
        inspector = inspect(self.engine)
        columns = {c["name"] for c in inspector.get_columns("accounts")}

        with self.engine.begin() as conn:
            if "instance_down_since" not in columns:
                conn.execute(
                    text("ALTER TABLE accounts ADD COLUMN instance_down_since DATETIME")
                )
                log.info("Added instance_down_since column to accounts table")
            if "source_removed_since" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE accounts ADD COLUMN source_removed_since DATETIME"
                    )
                )
                log.info("Added source_removed_since column to accounts table")

            id_column = next(
                (c for c in inspector.get_columns("accounts") if c["name"] == "id"),
                None,
            )
            if id_column and not id_column.get("nullable"):
                conn.execute(text("ALTER TABLE accounts ALTER COLUMN id DROP NOT NULL"))
                log.info("Made accounts.id nullable")

    @contextmanager
    def get_session(self):
        with self.Session() as session:
            yield session
