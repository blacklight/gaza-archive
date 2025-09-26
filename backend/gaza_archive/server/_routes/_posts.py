from fastapi import APIRouter, HTTPException

from ...model import Account, Post
from .. import ctx

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.get("", response_model=list[Post])
def get_posts(limit: int = 1000, offset: int | None = None) -> list[Post]:
    """
    List all posts.

    :param limit: Maximum number of posts to return (default: 1000).
    :param offset: Number of posts to skip before starting to collect the result set.
    :return: List of posts.
    """
    return list(ctx.db.get_accounts(limit=limit, offset=offset).values())


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

    db_account = ctx.db.get_account(account_url)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account
