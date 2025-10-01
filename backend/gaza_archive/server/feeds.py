import xml.etree.ElementTree as ET

from ..config import Config
from ..model import Account, Media, Post


class FeedsGenerator:
    def __init__(self, config: Config):
        self.config = config

    def generate_accounts_feed(self, accounts: list[Account]) -> str:
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        title = ET.SubElement(channel, "title")
        title.text = "Accounts Feed"

        link = ET.SubElement(channel, "link")
        link.text = self.config.base_url

        description = ET.SubElement(channel, "description")
        description.text = "RSS feed of accounts"

        for account in accounts:
            item = ET.SubElement(channel, "item")

            item_title = ET.SubElement(item, "title")
            item_title.text = account.display_name or account.username

            item_link = ET.SubElement(item, "link")
            item_link.text = account.url

            item_description = ET.SubElement(item, "description")
            item_description.text = f"Account: {account.username} on {account.instance}"

            guid = ET.SubElement(item, "guid")
            guid.text = account.url

        return ET.tostring(rss, encoding="utf-8").decode("utf-8")

    def generate_posts_feed(self, posts: list[Post], account: Account | None = None) -> str:
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        title = ET.SubElement(channel, "title")
        title.text = "Posts Feed"
        link = ET.SubElement(channel, "link")
        description = ET.SubElement(channel, "description")

        if account:
            title.text += f" for {account.fqn}"
            link.text = self.config.base_url + f"/accounts/{account.fqn}"
            description.text = f"Posts by {account.fqn}"
        else:
            link.text = self.config.base_url + "/posts"
            description.text = "Feed containing recent posts from all verified accounts in Gaza"

        for post in posts:
            item = ET.SubElement(channel, "item")

            post_content = (post.content or '').strip()
            item_title = ET.SubElement(item, "title")
            item_title.text = post_content[:30] + "..." if len(post_content) > 30 else post_content

            item_link = ET.SubElement(item, "link")
            item_link.text = post.url

            item_description = ET.SubElement(item, "description")
            item_description.text = post.content

            guid = ET.SubElement(item, "guid")
            guid.text = post.url

            pub_date = ET.SubElement(item, "pubDate")
            if post.created_at:
                pub_date.text = post.created_at.isoformat()

        return ET.tostring(rss, encoding="utf-8").decode("utf-8")

    def generate_media_feed(self, media_items: list[Media], account: Account | None = None) -> str:
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        title = ET.SubElement(channel, "title")
        title.text = "Media Feed"
        link = ET.SubElement(channel, "link")
        description = ET.SubElement(channel, "description")

        if account:
            title.text += f" for {account.fqn}"
            link.text = self.config.base_url + f"/accounts/{account.fqn}/media"
            description.text = f"Media by {account.fqn}"
        else:
            link.text = self.config.base_url + "/media"
            description.text = "Feed containing recent media from all verified accounts in Gaza"

        for media in media_items:
            item = ET.SubElement(channel, "item")

            item_title = ET.SubElement(item, "title")
            item_title.text = media.description or "Media Item"

            item_link = ET.SubElement(item, "link")
            item_link.text = self.config.base_url + media.path

            item_description = ET.SubElement(item, "description")
            item_description.text = f"Media Type: {media.type}"

            guid = ET.SubElement(item, "guid")
            guid.text = media.url
            pub_date = ET.SubElement(item, "pubDate")
            if media.post.created_at:
                pub_date.text = media.post.created_at.isoformat()

        return ET.tostring(rss, encoding="utf-8").decode("utf-8")
