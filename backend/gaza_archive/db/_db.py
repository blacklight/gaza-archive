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
        with self.engine.begin() as conn:
            self._migrate_accounts(conn)
            self._migrate_campaigns(conn)

    def _migrate_accounts(self, conn):
        """Apply migrations for the accounts table."""
        inspector = inspect(conn)
        if not inspector.has_table("accounts"):
            return

        columns = {c["name"] for c in inspector.get_columns("accounts")}

        if "instance_down_since" not in columns:
            conn.execute(
                text("ALTER TABLE accounts ADD COLUMN instance_down_since DATETIME")
            )
            log.info("Added instance_down_since column to accounts table")
        if "source_removed_since" not in columns:
            conn.execute(
                text("ALTER TABLE accounts ADD COLUMN source_removed_since DATETIME")
            )
            log.info("Added source_removed_since column to accounts table")

        id_column = next(
            (c for c in inspector.get_columns("accounts") if c["name"] == "id"),
            None,
        )
        if id_column and not id_column.get("nullable"):
            conn.execute(text("ALTER TABLE accounts ALTER COLUMN id DROP NOT NULL"))
            log.info("Made accounts.id nullable")

    def _migrate_campaigns(self, conn):
        """Apply migrations for the campaigns table."""
        inspector = inspect(conn)
        if not inspector.has_table("campaigns"):
            return

        campaign_columns = {c["name"] for c in inspector.get_columns("campaigns")}

        if "state" not in campaign_columns:
            conn.execute(
                text(
                    "ALTER TABLE campaigns ADD COLUMN state VARCHAR(20) DEFAULT 'ACTIVE'"
                )
            )
            log.info("Added state column to campaigns table")
        if "down_since" not in campaign_columns:
            conn.execute(text("ALTER TABLE campaigns ADD COLUMN down_since DATETIME"))
            log.info("Added down_since column to campaigns table")

    @contextmanager
    def get_session(self):
        with self.Session() as session:
            yield session
