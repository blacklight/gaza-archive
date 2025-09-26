from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model import Post
from ._model import Media as DbMedia, Post as DbPost

log = getLogger(__name__)


class Posts(ABC):
    """
    Database interface for posts.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def save_posts(self, posts: list[Post]):
        with self._write_lock, self.get_session() as session:
            db_posts: dict[str, DbPost] = {
                str(db_post.url): db_post
                for db_post in (
                    session.query(DbPost)
                    .filter(DbPost.url.in_([post.url for post in posts]))
                    .all()
                )
            }

            for post in posts:
                if post.url not in db_posts:
                    log.info(
                        "Adding new post with %d attachments: %s",
                        len(post.attachments),
                        post.url,
                    )
                    session.add(DbPost.from_model(post))

                    for media in post.attachments:
                        session.add(DbMedia.from_model(media))

            session.commit()
