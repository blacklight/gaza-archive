from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model import Account, Post
from ._model import Account as DbAccount, Media as DbMedia, Post as DbPost

log = getLogger(__name__)


class Posts(ABC):
    """
    Database interface for posts.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def get_posts(
        self,
        *,
        exclude_replies: bool = False,
        min_id: int | None = None,
        max_id: int | None = None,
        account: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Post]:
        with self.get_session() as session:
            query = session.query(DbPost, DbMedia).outerjoin(
                DbMedia, DbMedia.post_url == DbPost.url
            )

            if account is not None:
                query = query.join(
                    DbAccount, DbAccount.url == DbPost.author_url
                ).filter(DbAccount.url == Account.to_url(account))
            if min_id is not None:
                query = query.filter(DbPost.id > min_id)
            if max_id is not None:
                query = query.filter(DbPost.id < max_id)
            if exclude_replies:
                query = query.filter(DbPost.in_reply_to_id.is_(None))

            query = query.order_by(DbPost.created_at.desc())
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            db_posts = query.all()
            posts: dict[str, Post] = {}

            for db_post, db_media in db_posts:
                if db_post.id not in posts:
                    posts[db_post.url] = db_post.to_model()
                if db_media:
                    posts[db_post.url].attachments.append(db_media.to_model())

            return list(posts.values())

    def get_post(self, url: str) -> Post | None:
        with self.get_session() as session:
            db_post = session.query(DbPost).filter(DbPost.url == url).one_or_none()
            return db_post.to_model() if db_post else None

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
