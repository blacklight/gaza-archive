from fastapi import APIRouter, HTTPException, Response

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
def get_accounts(limit: int | None = None, offset: int | None = None) -> list[Account]:
    """
    Get all accounts.

    :param limit: Maximum number of accounts to return.
    :param offset: Number of accounts to skip before starting to collect the result set.
    :param rss: If True, return an RSS feed of the accounts.
    :return: List of accounts.
    """
    return list(get_ctx().db.get_accounts(limit=limit, offset=offset).values())


@router.get("/rss", response_model=str)
def get_accounts_feed(limit: int | None = None, offset: int | None = None) -> Response:
    """
    Get all accounts (RSS feed).

    :param limit: Maximum number of accounts to return.
    :param offset: Number of accounts to skip before starting to collect the result set.
    :param rss: If True, return an RSS feed of the accounts.
    :return: List of accounts.
    """
    ctx = get_ctx()
    accounts = list(ctx.db.get_accounts(limit=limit, offset=offset).values())
    return Response(
        content=FeedsGenerator(ctx.config).generate_accounts_feed(accounts),
        media_type="application/rss+xml",
    )


@router.get("/{account}", response_model=Account)
def get_account(account: str) -> Account:
    """
    Get account by URL.

    :param account: Account FQN, in the format `@username@instance`, or full URL.
    :return: Account object, or 404 if not found.
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
    account: str,
    exclude_replies: bool = False,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Post]:
    """
    Get posts for a specific account.

    :param exclude_replies: Whether to exclude replies (default: False).
    :param account: Account FQN, in the format `@username@instance`, or full URL.
    :param min_id: Minimum post ID to return (exclusive).
    :param max_id: Maximum post ID to return (exclusive).
    :param limit: Maximum number of posts to return.
    :param offset: Number of posts to skip before starting to collect the result set.
    :return: List of posts.
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
    account: str,
    exclude_replies: bool = False,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Response:
    """
    Get posts for a specific account (RSS feed).

    :param exclude_replies: Whether to exclude replies (default: False).
    :param account: Account FQN, in the format `@username@instance`, or full URL.
    :param min_id: Minimum post ID to return (exclusive).
    :param max_id: Maximum post ID to return (exclusive).
    :param limit: Maximum number of posts to return.
    :param offset: Number of posts to skip before starting to collect the result set.
    :return: List of posts.
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
    account: str,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Media]:
    """
    Get media attachments for a specific account.

    :param account: Account FQN, in the format `@username@instance`, or full URL.
    :param min_id: Minimum media ID to return (exclusive).
    :param max_id: Maximum media ID to return (exclusive).
    :param limit: Maximum number of media items to return.
    :param offset: Number of media items to skip before starting to collect the result set.
    :return: List of media attachments.
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
    account: str,
    min_id: int | None = None,
    max_id: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Response:
    """
    Get media attachments for a specific account (RSS feed).

    :param account: Account FQN, in the format `@username@instance`, or full URL.
    :param min_id: Minimum media ID to return (exclusive).
    :param max_id: Maximum media ID to return (exclusive).
    :param limit: Maximum number of media items to return.
    :param offset: Number of media items to skip before starting to collect the result set.
    :return: List of media attachments.
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
