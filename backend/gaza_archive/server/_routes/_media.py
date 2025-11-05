from fastapi import APIRouter, HTTPException, Path, Query, Response

from ...model import Media
from .. import get_ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.get("", response_model=list[Media])
def get_attachments(
    min_id: int | None = Query(
        None, description="Minimum media ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum media ID to return (exclusive)."
    ),
    limit: int = Query(
        50,
        description="Maximum number of attachments to return (default: 50).",
        gt=0,
        le=100,
    ),
    offset: int | None = Query(
        None,
        description="Number of attachments to skip before starting to collect the result set.",
    ),
) -> list[Media]:
    """
    List all media.
    """
    return list(
        get_ctx().db.get_attachments(
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/rss", response_model=Response)
def get_attachments_feed(
    min_id: int | None = Query(
        None, description="Minimum media ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum media ID to return (exclusive)."
    ),
    limit: int = Query(
        50,
        description="Maximum number of attachments to return (default: 50).",
        gt=0,
        le=100,
    ),
    offset: int | None = Query(
        None,
        description="Number of attachments to skip before starting to collect the result set.",
    ),
) -> Response:
    """
    Get media (RSS feed).
    """
    ctx = get_ctx()
    media = list(
        ctx.db.get_attachments(
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )
    return Response(
        content=FeedsGenerator(ctx.config).generate_media_feed(media),
        media_type="application/rss+xml",
    )


@router.get("/{media}", response_model=Media)
def get_attachment(
    media: str = Path(..., description="Media URL."),
) -> Media:
    """
    Get a specific media by URL.
    """
    db_media = get_ctx().db.get_attachment(media)
    if not db_media:
        raise HTTPException(status_code=404, detail="Media not found")
    return db_media
