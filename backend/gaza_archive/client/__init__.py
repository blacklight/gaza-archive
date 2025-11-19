from ..config import Config
from ..db import Db
from ..model import Account
from ..storages import Storage

from .bots import MastodonAccountsBot
from .downloader import MediaDownloader
from .mastodon import MastodonApi
from .sources import sources
from .sources.campaigns import CampaignParser


class Client(
    CampaignParser,
    MastodonApi,
    MediaDownloader,
    MastodonAccountsBot,
):
    """
    External client facade to interact with APIs and download media.
    """

    def __init__(self, config: Config, storage: Storage, db: Db):
        self.config = config
        self.db = db
        self.storage = storage
        self.sources = [source(config) for source in sources if source is not None]
        super().__init__()

    def get_verified_accounts(self) -> list[Account]:
        return list(
            {
                account.url: account
                for source in self.sources
                for account in source.get_verified_accounts()
            }.values()
        )
