from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from typing import Any, Callable, Iterator, Generator

from ..config import Config
from ..errors import DownloadError
from ..model import Media

log = getLogger(__name__)


class Storage(ABC):
    """
    Base class for storage implementations.
    """

    config: Config

    @abstractmethod
    def exists(self, item: Media) -> bool: ...

    @abstractmethod
    @contextmanager
    def _download(self, item: Media) -> Iterator[Any]:
        """
        Context manager for downloading media.
        Yields a callable that returns a generator of bytes.
        """

    @abstractmethod
    def _save(self, handle: Any, data: bytes) -> None: ...

    def save(
        self,
        item: Media,
        get_data: Callable[[], Generator[bytes, None, None]],
    ) -> None:
        try:
            with self._download(item) as handle:
                for chunk in get_data():
                    self._save(handle, chunk)
        except Exception as exc:
            try:
                self.delete(item)
            except Exception:
                pass

            log.exception(exc)
            raise DownloadError(f"Failed to save media {item.url}") from exc

    @abstractmethod
    def delete(self, item: Media) -> None: ...
