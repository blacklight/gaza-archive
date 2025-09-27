from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model import Account, Media as MediaModel
from ._model import Account as DbAccount, Media as DbMedia, Post as DbPost

log = getLogger(__name__)


class Media(ABC):
    """
    Database interface for media attachments.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def get_attachments(
        self,
        *,
        min_id: int | None = None,
        max_id: int | None = None,
        account: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[MediaModel]:
        with self.get_session() as session:
            query = session.query(DbMedia).join(DbPost, DbMedia.post_url == DbPost.url)

            if account is not None:
                query = query.join(
                    DbAccount, DbAccount.url == DbPost.author_url
                ).filter(DbAccount.url == Account.to_url(account))
            if min_id is not None:
                query = query.filter(DbMedia.id > min_id)
            if max_id is not None:
                query = query.filter(DbMedia.id < max_id)

            query = query.order_by(DbMedia.id.desc())
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            return [attachment.to_model() for attachment in query.all()]

    def get_attachment(self, url: str) -> MediaModel | None:
        with self.get_session() as session:
            db_media = session.query(DbMedia).filter(DbMedia.url == url).one_or_none()
            return db_media.to_model() if db_media else None
