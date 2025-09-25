from dataclasses import dataclass

from ._base import Item


@dataclass
class Media(Item):
    """
    Media class representing media attachments in posts.
    """

    id: str
    type: str
    description: str | None = None
    post_url: str | None = None

    def __eq__(self, other) -> bool:
        """
        Compare two Media instances for equality.
        """
        if not isinstance(other, Media):
            return False

        return (
            self.url == other.url
            and self.id == other.id
            and self.type == other.type
            and self.description == other.description
            and self.post_url == other.post_url
        )
