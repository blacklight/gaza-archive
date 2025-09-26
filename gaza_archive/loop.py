import logging
from threading import Event, Thread
from time import time

from .config import Config
from .db import Db
from .media import MediaDownloader
from .model import Account
from .scrapers import Api
from .storages import FileStorage

log = logging.getLogger(__name__)


class Loop(Thread):
    """
    Main loop class.
    """

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = Api(config)
        self.config = config
        self.storage = FileStorage(config)
        self.downloader = MediaDownloader(config=config, storage=self.storage)
        self.db = Db(self.config)
        self._stop_event = Event()

    def _main(self):
        """
        Main loop
        """
        if not self.config.enable_crawlers:
            log.info("Crawlers are disabled. Exiting.")
            return

        while not self._stop_event.is_set():
            try:
                self.refresh_accounts()
            except Exception as e:
                log.error("Error in main loop: %s", e)
                log.exception(e)
            finally:
                self._stop_event.wait(self.config.poll_interval)

    def refresh_accounts(self) -> list[Account]:
        log.info("Refreshing accounts...")
        t_start = time()

        verified_accounts = self.api.get_verified_accounts()
        accounts = self.api.refresh_accounts(verified_accounts)
        for account in accounts:
            if account.url in self.db._accounts:
                db_account = self.db._accounts[account.url]
                account.last_status_id = db_account.last_status_id

        posts = self.api.refresh_posts(accounts)

        self.db.save_accounts(accounts)
        self.db.save_posts(posts)

        if self.config.download_media:
            self.downloader.download_attachments(posts)

        log.info(
            "Refreshed %d accounts in %.2f seconds.", len(accounts), time() - t_start
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
