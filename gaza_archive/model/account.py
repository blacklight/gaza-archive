from dataclasses import dataclass

from ._base import Item


@dataclass
class Account(Item):
    """
    Account class representing user account information.
    """

    @property
    def username(self) -> str:
        return self.url.split("/")[-1]
