import logging
from threading import Event, Thread
from time import time

from .client import Client
from .config import Config
from .db import Db
from .model import Account, Campaign
from .storages import FileStorage

log = logging.getLogger(__name__)
_client: Client | None = None


def get_client() -> Client | None:
    return _client


class Loop(Thread):
    """
    Main loop class.
    """

    def __init__(self, config: Config, db: Db, *args, **kwargs):
        global _client

        super().__init__(*args, **kwargs)
        self.db = db
        self.config = config
        self.storage = FileStorage(config)
        self.client = _client = Client(config=config, storage=self.storage, db=db)
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
                accounts = self.refresh_accounts()
                self.refresh_campaigns(accounts)
            except Exception as e:
                log.error("Error in main loop: %s", e)
                log.exception(e)
            finally:
                self._stop_event.wait(self.config.poll_interval)

    def refresh_accounts(self) -> list[Account]:
        log.info("Refreshing accounts...")
        t_start = time()

        verified_accounts = self.client.get_verified_accounts()
        accounts = self.client.refresh_accounts(verified_accounts)
        for account in accounts:
            if account.url in self.db._accounts:  # pylint: disable=protected-access
                db_account = self.db._accounts[  # pylint: disable=protected-access
                    account.url
                ]
                account.last_status_id = db_account.last_status_id

        posts = self.client.refresh_posts(accounts)
        self.db.save_accounts(accounts)
        self.db.save_posts(posts)
        self.client.boost_posts(posts)

        if self.config.download_media:
            self.client.download_account_images(accounts)
            self.client.download_attachments(posts)

        log.info(
            "Refreshed %d accounts in %.2f seconds.", len(accounts), time() - t_start
        )
        return accounts

    def refresh_campaigns(self, accounts: list[Account]) -> list[Campaign]:
        campaigns = self.client.refresh_campaigns(accounts)
        self.db.save_campaigns(campaigns)
        return campaigns

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
