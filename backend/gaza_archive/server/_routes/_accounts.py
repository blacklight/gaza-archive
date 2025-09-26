from fastapi import APIRouter, HTTPException

from ...model import Account
from .. import ctx

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[Account])
def get_accounts(limit: int | None = None, offset: int | None = None) -> list[Account]:
    """
    Get all accounts.

    :param limit: Maximum number of accounts to return.
    :param offset: Number of accounts to skip before starting to collect the result set.
    :return: List of accounts.
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
