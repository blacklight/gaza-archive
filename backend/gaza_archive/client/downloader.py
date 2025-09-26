from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger

import requests

from ..config import Config
from ..errors import DownloadError
from ..model import Media, Post
from ..storages import Storage

log = getLogger(__name__)


class MediaDownloader(ABC):
    config: Config
    storage: Storage

    def download(self, item: Media):
        if self.storage.exists(item):
            log.debug("Attachment already downloaded: %s", item.url)
            return

        log.info(
            "Downloading attachment %s to [%s]/%s",
            item.url,
            self.storage.__class__.__name__,
            item.path,
        )

        try:
            with requests.get(
                item.url,
                stream=True,
                timeout=self.storage.config.http_timeout,
                headers={"User-Agent": self.storage.config.user_agent},
            ) as response:
                response.raise_for_status()
                self.storage.save(
                    item,
                    lambda: (chunk for chunk in response.iter_content(chunk_size=8192)),
                )
        except Exception as exc:
            raise DownloadError(f"Failed to download media {item.url}") from exc

    def download_post_attachments(self, post: Post):
        attachments = [media for media in post.attachments if isinstance(media, Media)]
        if not attachments:
            return

        for media in attachments:
            self.download(media)

    def download_attachments(self, posts: list[Post]):
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            for post in posts:
                executor.submit(self.download_post_attachments, post)
