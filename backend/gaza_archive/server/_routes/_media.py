from fastapi import APIRouter, HTTPException

from ...model import Media
from .. import ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.get("", response_model=list[Media])
def get_attachments(
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int = 50,
    offset: int | None = None,
) -> list[Media]:
    """
    List all media.

    :param min_id: Minimum media ID to return (exclusive).
    :param max_id: Maximum media ID to return (exclusive).
    :param limit: Maximum number of attachments to return (default: 50).
    :param offset: Number of attachments to skip before starting to collect the result set.
    :return: List of attachments.
    """
    return list(
        ctx.db.get_attachments(
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/rss", response_model=str)
def get_attachments_feed(
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int = 50,
    offset: int | None = None,
) -> str:
    """
    Get media (RSS feed).

    :param min_id: Minimum media ID to return (exclusive).
    :param max_id: Maximum media ID to return (exclusive).
    :param limit: Maximum number of attachments to return (default: 50).
    :param offset: Number of attachments to skip before starting to collect the result set.
    :return: RSS feed of media.
    """
    media = list(
        ctx.db.get_attachments(
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )
    return FeedsGenerator(ctx.config).generate_media_feed(media)


@router.get("/{media}", response_model=Media)
def get_attachment(media: str) -> Media:
    """
    Get a specific media by URL.

    :param media: Media URL.
    :return: The media object, or 404 if not found.
    """
    db_media = ctx.db.get_attachment(media)
    if not db_media:
        raise HTTPException(status_code=404, detail="Media not found")
    return db_media
