from fastapi import APIRouter, HTTPException, Query, Response

from ...model import Account, Media, Post
from .. import get_ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


def _get_account_posts(
    account: str,
    exclude_replies: bool = False,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Post]:
    try:
        account_url = Account.to_url(account)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid account format: {e}"
        ) from e

    ctx = get_ctx()
    db_account = ctx.db.get_account(account_url)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    return list(
        ctx.db.get_posts(
            exclude_replies=exclude_replies,
            account=account_url,
            min_id=min_id,
            max_id=max_id,
            limit=limit,
            offset=offset,
        )
    )


def _get_account_media(
    account: str,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Media]:
    try:
        account_url = Account.to_url(account)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid account format: {e}"
        ) from e

    ctx = get_ctx()
    db_account = ctx.db.get_account(account_url)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    return ctx.db.get_attachments(
        account=account_url,
        min_id=min_id,
        max_id=max_id,
        limit=limit,
        offset=offset,
    )


@router.get("", response_model=list[Account])
def get_accounts(
    limit: int | None = Query(
        None, description="Maximum number of accounts to return."
    ),
    offset: int | None = Query(
        None,
        description="Number of accounts to skip before starting to collect the result set.",
    ),
) -> list[Account]:
    """
    Get all accounts.
    """
    return list(get_ctx().db.get_accounts(limit=limit, offset=offset).values())


@router.get("/rss", response_model=str)
def get_accounts_feed(
    limit: int | None = Query(
        None, description="Maximum number of accounts to return."
    ),
    offset: int | None = Query(
        None,
        description="Number of accounts to skip before starting to collect the result set.",
    ),
) -> Response:
    """
    Get all accounts (RSS feed).
    """
    ctx = get_ctx()
    accounts = list(ctx.db.get_accounts(limit=limit, offset=offset).values())
    return Response(
        content=FeedsGenerator(ctx.config).generate_accounts_feed(accounts),
        media_type="application/rss+xml",
    )


@router.get("/{account}", response_model=Account)
def get_account(
    account: str = Query(
        ...,
        description="Account FQN, in the format `@username@instance`, or full URL.",
    )
) -> Account:
    """
    Get account by URL.
    """
    try:
        account_url = Account.to_url(account)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid account format: {e}"
        ) from e

    db_account = get_ctx().db.get_account(account_url)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account


@router.get("/{account}/posts", response_model=list[Post])
def get_account_posts(
    account: str = Query(
        ...,
        description="Account FQN, in the format `@username@instance`, or full URL.",
    ),
    exclude_replies: bool = Query(
        False, description="Whether to exclude replies (default: False)."
    ),
    min_id: int | None = Query(
        None, description="Minimum post ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum post ID to return (exclusive)."
    ),
    limit: int | None = Query(None, description="Maximum number of posts to return."),
    offset: int | None = Query(
        None,
        description="Number of posts to skip before starting to collect the result set.",
    ),
) -> list[Post]:
    """
    Get posts for a specific account.
    """
    return _get_account_posts(
        account=account,
        exclude_replies=exclude_replies,
        min_id=min_id,
        max_id=max_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{account}/posts/rss", response_model=str)
def get_account_posts_feed(
    account: str = Query(
        ...,
        description="Account FQN, in the format `@username@instance`, or full URL.",
    ),
    exclude_replies: bool = Query(
        False, description="Whether to exclude replies (default: False)."
    ),
    min_id: int | None = Query(
        None, description="Minimum post ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum post ID to return (exclusive)."
    ),
    limit: int | None = Query(None, description="Maximum number of posts to return."),
    offset: int | None = Query(
        None,
        description="Number of posts to skip before starting to collect the result set.",
    ),
) -> Response:
    """
    Get posts for a specific account (RSS feed).
    """
    posts = _get_account_posts(
        account=account,
        exclude_replies=exclude_replies,
        min_id=min_id,
        max_id=max_id,
        limit=limit,
        offset=offset,
    )

    ctx = get_ctx()
    return Response(
        content=FeedsGenerator(ctx.config).generate_posts_feed(
            posts=posts, account=ctx.db.get_account(Account.to_url(account))
        ),
        media_type="application/rss+xml",
    )


@router.get("/{account}/media", response_model=list[Media])
def get_account_media(
    account: str = Query(
        ...,
        description="Account FQN, in the format `@username@instance`, or full URL.",
    ),
    min_id: int | None = Query(
        None, description="Minimum media ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum media ID to return (exclusive)."
    ),
    limit: int | None = Query(
        None, description="Maximum number of media items to return."
    ),
    offset: int | None = Query(
        None,
        description="Number of media items to skip before starting to collect the result set.",
    ),
) -> list[Media]:
    """
    Get media attachments for a specific account.
    """
    return _get_account_media(
        account=account,
        min_id=min_id,
        max_id=max_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{account}/media/rss", response_model=str)
def get_account_media_feed(
    account: str = Query(
        ...,
        description="Account FQN, in the format `@username@instance`, or full URL.",
    ),
    min_id: int | None = Query(
        None, description="Minimum media ID to return (exclusive)."
    ),
    max_id: int | None = Query(
        None, description="Maximum media ID to return (exclusive)."
    ),
    limit: int | None = Query(
        None, description="Maximum number of media items to return."
    ),
    offset: int | None = Query(
        None,
        description="Number of media items to skip before starting to collect the result set.",
    ),
) -> Response:
    """
    Get media attachments for a specific account (RSS feed).
    """
    media = _get_account_media(
        account=account,
        min_id=min_id,
        max_id=max_id,
        limit=limit,
        offset=offset,
    )

    ctx = get_ctx()
    return Response(
        content=FeedsGenerator(ctx.config).generate_media_feed(
            media, account=ctx.db.get_account(Account.to_url(account))
        ),
        media_type="application/rss+xml",
    )
