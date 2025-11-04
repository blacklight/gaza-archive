from datetime import datetime
from typing import Collection

from fastapi import APIRouter, Query

from ...model import ApiSortType, CampaignStats, api_split_args
from .. import get_ctx

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])

def _get_campaigns(
    accounts: str | Collection[str] | None = None,
    donors: str | Collection[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    group_by: str | Collection[str] | None = None,
    sort: str | Collection[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    currency: str | None = None,
) -> CampaignStats:
    accounts = api_split_args(accounts) if accounts else None
    donors = api_split_args(donors) if donors else None
    start_time = (
        datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if start_time else None
    )
    end_time = (
        datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        if end_time else None
    )
    group_by = api_split_args(group_by) if group_by else None
    sort = (
        [
            ApiSortType.parse(arg)
            for arg in api_split_args(sort)
        ]
        if sort else None
    )

    return get_ctx().db.get_campaigns(
        accounts=accounts,
        donors=donors,
        start_time=start_time,
        end_time=end_time,
        group_by=group_by,
        sort=sort,
        limit=limit,
        offset=offset,
        currency=currency,
    )


@router.get("/accounts")
def get_accounts_campaigns(
    accounts: str | list[str] | None = Query(None),
    donors: str | list[str] | None = Query(None),
    start_time: str | None = None,
    end_time: str | None = None,
    group_by: str | list[str] | None = Query(None),
    sort: str | list[str] | None = Query(None),
    limit: int | None = None,
    offset: int | None = None,
    currency: str | None = None,
) -> CampaignStats:
    """
    Get account campaign stats.

    :param accounts: Filter by account URLs or FQDNs.
    :param donors: Filter by donor names.
    :param start_time: Filter donations created after this time (ISO 8601 format).
    :param end_time: Filter donations created before this time (ISO 8601 format).
    :param group_by: Fields to group by (e.g., "account.url", "donation.donor").
        Date units are also supported (e.g., "donation.created_at:day",
        "donation.created_at:week", "donation.created_at:month", "donation.created_at:year").
    :param sort: Fields to sort by (e.g., "amount", "donation.created_at"). Add ":desc" for descending order.
    :param limit: Maximum number of results to return.
    :param offset: Number of results to skip before starting to collect the result set.
    :param currency: Currency code for amounts (default: USD).
    :return: Campaign stats.
    """
    if not group_by:
        group_by = []
    if "account.url" not in group_by:
        group_by = ["account.url"] + list(group_by or [])

    return _get_campaigns(
        accounts=accounts,
        donors=donors,
        start_time=start_time,
        end_time=end_time,
        group_by=group_by,
        sort=sort,
        limit=limit,
        offset=offset,
        currency=currency,
    )


@router.get("/accounts/{account}")
def get_accounts_campaigns(
        account: str,
        donors: str | list[str] | None = Query(None),
        start_time: str | None = None,
        end_time: str | None = None,
        group_by: str | list[str] | None = Query(None),
        sort: str | list[str] | None = Query(None),
        limit: int | None = None,
        offset: int | None = None,
        currency: str | None = None,
) -> CampaignStats:
    """
    Get campaign stats for a specific account.

    :param account: Account URL or FQDN.
    :param donors: Filter by donor names.
    :param start_time: Filter donations created after this time (ISO 8601 format).
    :param end_time: Filter donations created before this time (ISO 8601 format).
    :param group_by: Fields to group by (e.g., "account_url", "donor").
        Date units are also supported
        (e.g., "created_at:day", "created_at:week", "created_at:month", "created_at:year").
    :param sort: Fields to sort by (e.g., "amount", "created_at"). Add ":desc" for descending order.
    :param limit: Maximum number of results to return.
    :param offset: Number of results to skip before starting to collect the result set.
    :param currency: Currency code for amounts (default: USD).
    :return: Campaign stats.
    """
    if not group_by:
        group_by = []
    if "account.url" not in group_by:
        group_by = ["account.url"] + list(group_by or [])

    return _get_campaigns(
        accounts=[account],
        donors=donors,
        start_time=start_time,
        end_time=end_time,
        group_by=group_by,
        sort=sort,
        limit=limit,
        offset=offset,
        currency=currency,
    )
