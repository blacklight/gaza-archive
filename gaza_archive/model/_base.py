from abc import ABC
from dataclasses import dataclass


@dataclass
class Item(ABC):
    """
    Base class for item implementations.
    """

    url: str
