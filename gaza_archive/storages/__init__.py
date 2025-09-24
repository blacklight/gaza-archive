from abc import ABC, abstractmethod

from ..items import Item


class Storage(ABC):
    """
    Base class for storage implementations.
    """

    @abstractmethod
    def get(self, url: str):
        pass

    @abstractmethod
    def save(self, item: Item):
        pass

    @abstractmethod
    def delete(self, url: str):
        pass
