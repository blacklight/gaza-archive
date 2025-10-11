from urllib.parse import unquote

from fastapi import APIRouter, HTTPException

from ...model import Post
from .. import get_ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.get("", response_model=list[Post])
def get_posts(
    exclude_replies: bool = False,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int = 50,
    offset: int | None = None,
) -> list[Post]:
    """
    List all posts.

    :param exclude_replies: Whether to exclude replies (default: False).
    :param min_id: Minimum post ID to return (exclusive).
    :param max_id: Maximum post ID to return (exclusive).
    :param limit: Maximum number of posts to return (default: 50).
    :param offset: Number of posts to skip before starting to collect the result set.
    :return: List of posts.
    """
    return list(
        get_ctx().db.get_posts(
            exclude_replies=exclude_replies,
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/rss", response_model=str)
def get_posts_feed(
    exclude_replies: bool = False,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int = 50,
    offset: int | None = None,
) -> str:
    """
    Get posts (RSS feed).

    :param exclude_replies: Whether to exclude replies (default: False).
    :param min_id: Minimum post ID to return (exclusive).
    :param max_id: Maximum post ID to return (exclusive).
    :param limit: Maximum number of posts to return (default: 50).
    :param offset: Number of posts to skip before starting to collect the result set.
    :return: RSS feed of posts.
    """
    ctx = get_ctx()
    posts = list(
        ctx.db.get_posts(
            exclude_replies=exclude_replies,
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )
    return FeedsGenerator(ctx.config).generate_posts_feed(posts)


@router.get("/{post}", response_model=Post)
def get_post(post: str) -> Post:
    """
    Get a specific post by URL or ID.

    :param post: Post URL.
    :return: The post object, or 404 if not found.
    """
    db_post = get_ctx().db.get_post(unquote(post))
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post
