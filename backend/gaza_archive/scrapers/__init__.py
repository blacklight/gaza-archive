from ..config import Config
from .gaza_verified import GazaVerifiedApi
from .mastodon import MastodonApi


class Api(GazaVerifiedApi, MastodonApi):
    """
    Main API facade.
    """

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
