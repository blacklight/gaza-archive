from ..config import Config
from ..model import Account
from ..storages import Storage

from .downloader import MediaDownloader
from .mastodon import MastodonApi
from .sources import sources
from .sources.campaigns import CampaignParser


class Client(MastodonApi, MediaDownloader):
    """
    External client facade to interact with APIs and download media.
    """

    def __init__(self, config: Config, storage: Storage):
        super().__init__()
        self.config = config
        self.storage = storage
        self.campaign_parser = CampaignParser()
        self.sources = [source(config) for source in sources if source is not None]

    def get_verified_accounts(self) -> list[Account]:
        return list(
            {
                account.url: account
                for source in self.sources
                for account in source.get_verified_accounts()
            }.values()
        )
