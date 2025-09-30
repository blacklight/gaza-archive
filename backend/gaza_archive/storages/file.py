import logging
import os
import pathlib
from contextlib import contextmanager
from typing import IO, Iterator

from ..config import Config
from ..model import Media
from ._base import Storage

log = logging.getLogger(__name__)


class FileStorage(Storage):
    """
    File-based storage implementation.
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.basedir = os.path.abspath(os.path.expanduser(config.storage_path))
        self.media_dir = self.basedir
        if not self.media_dir.endswith("/media"):
            self.media_dir += "media"

        pathlib.Path(self.media_dir).mkdir(parents=True, exist_ok=True)
        log.info("File storage initialized at %s", self.basedir)

    def exists(self, item: Media):
        filename = os.path.join(self.media_dir, item.path)
        return os.path.exists(filename)

    @contextmanager
    def _download(self, item: Media) -> Iterator[IO]:
        media_path = os.path.join(self.media_dir, item.path.lstrip("/"))
        log.info("Downloading attachment %s to %s", item.url, media_path)
        pathlib.Path(os.path.dirname(media_path)).mkdir(parents=True, exist_ok=True)
        with open(media_path, "wb") as handle:
            yield handle

    def _save(self, handle: IO, data: bytes) -> None:
        handle.write(data)

    def delete(self, item: Media):
        filename = os.path.join(self.media_dir, item.path)
        if os.path.exists(filename):
            os.remove(filename)
