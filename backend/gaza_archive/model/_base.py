from abc import ABC

from pydantic import BaseModel


class Item(BaseModel, ABC):
    """
    Base class for item implementations.
    """

    url: str
