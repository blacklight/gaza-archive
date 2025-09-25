import logging
from threading import Event, Thread
from time import time

from .config import Config
from .db import Db
from .model import Account
from .scrapers import Api

log = logging.getLogger(__name__)


class Loop(Thread):
    """
    Main loop class.
    """

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = Api(config)
        self.config = config
        self.db = Db(self.config)
        self._stop_event = Event()

    def _main(self):
        """
        Main loop
        """
        while not self._stop_event.is_set():
            try:
                self.refresh_accounts()
            except Exception as e:
                log.error("Error in main loop: %s", e)
            finally:
                self._stop_event.wait(self.config.poll_interval)

    def refresh_accounts(self) -> list[Account]:
        log.info("Refreshing accounts...")
        t_start = time()
        accounts = self.api.refresh_accounts(self.api.get_verified_accounts())

        # TODO Fetch account activity here

        self.db.save_accounts(accounts)
        log.info(
            "Fetched %d accounts in %.2f seconds.", len(accounts), time() - t_start
        )
        return accounts

    def run(self):
        """
        Run the main loop.
        """
        super().run()
        self._main()

    def stop(self):
        """
        Stop the main loop.
        """
        self._stop_event.set()
