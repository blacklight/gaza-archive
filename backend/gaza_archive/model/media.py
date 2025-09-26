from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import computed_field

from ._base import Item

if TYPE_CHECKING:
    from .post import Post


class Media(Item):
    """
    Media class representing media attachments in posts.
    """

    id: str
    type: str
    post: Post = None  # type: ignore[assignment]
    description: str | None = None

    @computed_field
    @property
    def path(self) -> str:
        """
        :return: The file path for storing the media, formatted as
            "username/post_id.extension".
        """
        return f"/{self.post.author.username}/{self.id}.{self.url.split('.')[-1]}"
