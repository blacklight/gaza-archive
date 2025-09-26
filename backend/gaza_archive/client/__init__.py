from ..config import Config
from ..storages import Storage
from .downloader import MediaDownloader
from .gaza_verified import GazaVerifiedApi
from .mastodon import MastodonApi


class Client(GazaVerifiedApi, MastodonApi, MediaDownloader):
    """
    External client facade to interact with APIs and download media.
    """

    def __init__(self, config: Config, storage: Storage):
        super().__init__()
        self.config = config
        self.storage = storage
