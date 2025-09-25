from dataclasses import dataclass, field
from datetime import datetime

from ._base import Item
from .media import Media


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
    attachments: list[Media] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
