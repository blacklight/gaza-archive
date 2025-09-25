import logging
from threading import Event, Thread

from .api import Api
from .db import Db
from .config import Config
from .model import Account

log = logging.getLogger(__name__)


class Loop(Thread):
    """
    Main loop class.
    """

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accounts: dict[str, Account] = {}
        self.api = Api(config)
        self.config = config
        self.db = Db(self.config)
        self._stop_event = Event()

    def _main(self):
        """
        Main async loop
        """
        while not self._stop_event.is_set():
            try:
                accounts = self.api.get_accounts()
                print(accounts)
                # for account in accounts:
                #     self.fetch_account_activity(account)
                #     break  # TODO
            except Exception as e:
                log.error("Error in main loop: %s", e)
            finally:
                self._stop_event.wait(self.config.poll_interval)

    # def fetch_account_activity(self, account: Account) -> list[Item]:
    #     items = []
    #     log.info("Fetching activity for account: %s", account.username)
    #     print(account.apiURL)
    #     response = requests.get(
    #         account.apiURL,
    #         timeout=self.config.http_timeout,
    #         headers={"User-Agent": self.config.user_agent},
    #     )

    #     print(response.text)

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
