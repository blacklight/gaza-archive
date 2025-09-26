from ...model import Account
from .. import ctx

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[Account])
def get_accounts(limit: int | None = None, offset: int | None = None) -> list[Account]:
    """
    Get all accounts.
    """
    return list(ctx.db.get_accounts(limit=limit, offset=offset).values())
