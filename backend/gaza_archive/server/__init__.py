from logging import getLogger
from threading import Thread

import uvicorn

from ..config import Config
from ..db import Db
from ._app import app

log = getLogger(__name__)


class ApiServer(Thread):
    """
    API server class.
    """

    def __init__(self, config: Config, db: Db, *_, **__):
        super().__init__()
        self.config = config
        self.db = db

    def run(self):
        super().run()
        try:
            uvicorn.run(
                app,
                host=self.config.api_host,
                port=self.config.api_port,
                log_level="debug" if self.config.debug else "info",
            )
        except KeyboardInterrupt:
            pass
        except Exception as e:
            log.error("Failed to start API server: %s", e)
            raise
