from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timezone
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model import BotState
from ._model import BotState as DbBotState

log = getLogger(__name__)


class Bots(ABC):
    """
    Database interface for bot states.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def get_bot_state(self, bot_name: str) -> BotState | None:
        with self.get_session() as session:
            bot_state = session.query(DbBotState).get(bot_name)
            return bot_state.to_model() if bot_state else None

    def refresh_bot_state(self, bot_name: str):
        with self.get_session() as session:
            bot_state = session.query(DbBotState).get(bot_name)
            if bot_state:
                bot_state.last_updated_at = datetime.now(timezone.utc)
            else:
                bot_state = DbBotState(
                    bot_name=bot_name,
                    last_updated_at=datetime.now(timezone.utc),
                )

            session.add(bot_state)
            session.commit()
