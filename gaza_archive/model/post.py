from dataclasses import dataclass
from datetime import datetime

from ._base import Item


@dataclass
class Post(Item):
    """
    Post class representing a social media post.
    """

    id: str
    author_url: str
    content: str | None = None
    in_reply_to_id: str | None = None
    in_reply_to_account_id: str | None = None
    quote: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # TODO Add media
