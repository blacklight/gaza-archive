from __future__ import annotations
from datetime import datetime

from pydantic import Field

from ._base import Item
from .account import Account
from .media import Media


class Post(Item):
    """
    Post class representing a social media post.
    """

    id: str
    author: Account
    content: str | None = None
    in_reply_to_id: str | None = None
    in_reply_to_account_id: str | None = None
    quote: str | None = None
    attachments: list[Media] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
