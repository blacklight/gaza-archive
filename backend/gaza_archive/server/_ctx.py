from dataclasses import dataclass
from typing import Optional

from ..config import Config
from ..db import Db


@dataclass
class Context:
    """
    API server context.
    """

    config: Config
    db: Db


def get_ctx() -> Context:
    """
    Get the API server context.
    """
    global _ctx  # pylint: disable=global-statement

    if _ctx is None:
        config = Config.from_env()
        db = Db(config)
        _ctx = Context(config=config, db=db)

    return _ctx


_ctx: Optional[Context] = None
