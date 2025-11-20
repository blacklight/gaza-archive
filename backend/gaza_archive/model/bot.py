from dataclasses import dataclass
from datetime import datetime


@dataclass
class BotState:
    """
    Represents the state of a bot.
    """

    bot_name: str
    last_updated_at: datetime | None = None