from ..config import Config
from .gaza_verified import GazaVerifiedApi


class Api(GazaVerifiedApi):
    """
    Main API facade.
    """

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
