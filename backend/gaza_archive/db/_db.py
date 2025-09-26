from contextlib import contextmanager
from logging import getLogger
from threading import RLock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ._accounts import Accounts
from ._model import Base
from ._posts import Posts

log = getLogger(__name__)


class Db(Accounts, Posts):
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
        self._load_accounts()

    @contextmanager
    def get_session(self):
        with self.Session() as session:
            yield session
