from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Path, Query, Response

from ...model import Post
from .. import get_ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.get("", response_model=list[Post])
def get_posts(
    exclude_replies: bool = Query(
        False, description="Whether to exclude replies (default: False)."
    ),
    min_id: int | None = Query(
        None, description="Minimum post ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum post ID to return (exclusive)."
    ),
    limit: int = Query(
        50,
        description="Maximum number of posts to return (default: 50).",
        gt=0,
        le=100,
    ),
    offset: int | None = Query(
        None,
        description="Number of posts to skip before starting to collect the result set.",
    ),
) -> list[Post]:
    """
    List all posts.
    """
    ctx = get_ctx()
    if ctx.config.hide_replies:
        exclude_replies = True

    return list(
        ctx.db.get_posts(
            exclude_replies=exclude_replies,
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/rss", response_model=str)
def get_posts_feed(
    exclude_replies: bool = Query(
        False, description="Whether to exclude replies (default: False)."
    ),
    min_id: int | None = Query(
        None, description="Minimum post ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum post ID to return (exclusive)."
    ),
    limit: int = Query(
        50,
        description="Maximum number of posts to return (default: 50).",
        gt=0,
        le=100,
    ),
    offset: int | None = Query(
        None,
        description="Number of posts to skip before starting to collect the result set.",
    ),
) -> Response:
    """
    Get posts (RSS feed).
    """
    ctx = get_ctx()
    if ctx.config.hide_replies:
        exclude_replies = True

    posts = list(
        ctx.db.get_posts(
            exclude_replies=exclude_replies,
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )
    return Response(
        content=FeedsGenerator(ctx.config).generate_posts_feed(posts),
        media_type="application/rss+xml",
    )


@router.get("/{post}", response_model=Post)
def get_post(
    post: str = Path(
        ...,
        description="Post URL or ID.",
    ),
) -> Post:
    """
    Get a specific post by URL or ID.
    """
    ctx = get_ctx()
    db_post = ctx.db.get_post(unquote(post))
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if ctx.config.hide_replies and db_post.in_reply_to_id:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post
