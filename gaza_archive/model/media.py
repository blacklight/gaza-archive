from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._base import Item

if TYPE_CHECKING:
    from .post import Post


@dataclass
class Media(Item):
    """
    Media class representing media attachments in posts.
    """

    id: str
    type: str
    post: Post
    description: str | None = None

    @property
    def path(self) -> str:
        """
        Returns the path of the media item.
        """
        return f"{self.post.author.username}/{self.id}.{self.url.split('.')[-1]}"
