import os
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger

import requests

from ..config import Config
from ..errors import DownloadError
from ..model import Account, Media, Post
from ..storages import Storage

log = getLogger(__name__)


class MediaDownloader(ABC):
    config: Config
    storage: Storage

    def download(self, url: str, path: str):
        if self.storage.exists(path):
            log.debug("Attachment already downloaded: %s", url)
            return

        try:
            with requests.get(
                url,
                stream=True,
                timeout=self.storage.config.http_timeout,
                headers={"User-Agent": self.storage.config.user_agent},
            ) as response:
                response.raise_for_status()
                self.storage.save(
                    url,
                    path,
                    lambda: (chunk for chunk in response.iter_content(chunk_size=8192)),
                )
        except Exception as exc:
            raise DownloadError(f"Failed to download media {url}") from exc

    def download_post_attachments(self, post: Post):
        attachments = [media for media in post.attachments if isinstance(media, Media)]
        if not attachments:
            return

        for media in attachments:
            self.download(url=media.url, path=media.path)

    def download_attachments(self, posts: list[Post]):
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            for post in posts:
                executor.submit(self.download_post_attachments, post)

    def download_profile_image(self, account: Account):
        if (
            not account.avatar_path
            or not account.avatar_url
            or self.storage.exists(account.avatar_path)
        ):
            return

        log.info(
            "Downloading profile image for %s to %s", account.url, account.avatar_path
        )
        self.download(url=account.avatar_url, path=account.avatar_path)

    def download_header_image(self, account: Account):
        if (
            not account.header_path
            or not account.header_url
            or self.storage.exists(account.header_path)
        ):
            return

        log.info(
            "Downloading header image for %s to %s", account.url, account.header_path
        )
        self.download(url=account.header_url, path=account.header_path)

    def download_account_images(self, accounts: list[Account]):
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            for account in accounts:
                executor.submit(self.download_profile_image, account)
                executor.submit(self.download_header_image, account)
