from logging import getLogger

from .db import Db
from .config import Config
from .loop import Loop
from .server import ApiServer

log = getLogger(__name__)


class App:
    """
    Main application class.
    """

    def __init__(self):
        self.config = Config.from_env()
        self.db = Db(self.config)
        self.loop = Loop(config=self.config, db=self.db)
        self.api = ApiServer(config=self.config, db=self.db)

    def run(self):
        try:
            self.loop.start()
            self.api.start()
            self.loop.join()
        except KeyboardInterrupt:
            self.api.join()
            self.loop.stop()
            self.loop.join()
        finally:
            log.info("Exiting...")
