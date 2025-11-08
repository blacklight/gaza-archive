from datetime import datetime
from typing import Collection

from fastapi import APIRouter, Path, Query
from fastapi.responses import Response

from ...model import ApiSortType, CampaignDonationInfo, CampaignStats, api_split_args
from .. import get_ctx
from ..feeds import FeedsGenerator

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


def _get_campaigns(
    *,
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
    start_time_dt = (
        datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if start_time
        else None
    )
    end_time_dt = (
        datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None
    )
    group_by = api_split_args(group_by) if group_by else None
    sort_keys = (
        [ApiSortType.parse(arg) for arg in api_split_args(sort)] if sort else None
    )

    return get_ctx().db.get_campaigns(
        accounts=accounts,
        donors=donors,
        start_time=start_time_dt,
        end_time=end_time_dt,
        group_by=group_by,
        sort=sort_keys,
        limit=limit,
        offset=offset,
        currency=currency,
    )


def _get_donations(
    *,
    accounts: list[str] | None = None,
    donors: list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    sort: str | Collection[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    currency: str | None = None,
) -> list[CampaignDonationInfo]:
    """
    Get campaigns donations.
    """
    return get_ctx().db.get_donations(
        accounts=accounts,
        donors=donors,
        start_time=(
            datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if start_time
            else None
        ),
        end_time=(
            datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            if end_time
            else None
        ),
        sort=(
            [ApiSortType.parse(arg) for arg in api_split_args(sort)] if sort else None
        ),
        limit=limit,
        offset=offset,
        currency=currency,
    )


@router.get("/accounts", response_model=CampaignStats)
def get_accounts_campaigns(
    accounts: list[str] = Query(
        [],
        description="Filter by account URLs or FQDNs. Wildcards are supported.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    group_by: list[str] = Query(
        [],
        description=(
            'Fields to group by (e.g., "account.url", "donation.donor"). '
            'Date units are also supported (e.g., "donation.created_at:day", '
            '"donation.created_at:week", "donation.created_at:month", '
            '"donation.created_at:year").'
        ),
    ),
    sort: list[str] = Query(
        [],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int | None = Query(
        None,
        description="Maximum number of results to return.",
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
):
    """
    Get account campaigns stats.
    """
    if not group_by:
        group_by = []
    if "account.url" not in group_by:
        group_by = ["account.url"] + list(group_by or [])

    try:
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
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/accounts/{account}", response_model=CampaignStats)
def get_account_campaigns(
    account: str = Path(
        ...,
        description="Account URLs or FQDNs.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    group_by: list[str] = Query(
        [],
        description=(
            'Fields to group by (e.g., "account.url", "donation.donor"). '
            'Date units are also supported (e.g., "donation.created_at:day", '
            '"donation.created_at:week", "donation.created_at:month", '
            '"donation.created_at:year").'
        ),
    ),
    sort: list[str] = Query(
        [],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int | None = Query(
        None,
        description="Maximum number of results to return.",
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
):
    """
    Get campaign stats for a specific account.
    """
    if not group_by:
        group_by = []
    if "account.url" not in group_by:
        group_by = ["account.url"] + list(group_by or [])

    try:
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
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/donations", response_model=list[CampaignDonationInfo])
def get_donations(
    accounts: list[str] = Query(
        [],
        description="Filter by account URLs or FQDNs. Wildcards are supported.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    sort: list[str] = Query(
        [],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int = Query(
        50,
        description="Maximum number of results to return.",
        le=100,
        ge=1,
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
):
    """
    Get campaigns donations.
    """

    try:
        return _get_donations(
            accounts=accounts,
            donors=donors,
            start_time=start_time,
            end_time=end_time,
            sort=sort,
            limit=limit,
            offset=offset,
            currency=currency,
        )
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/accounts/{account}/donations", response_model=list[CampaignDonationInfo])
def get_account_donations(
    account: str = Path(
        ...,
        description="Account URLs or FQDNs.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    sort: list[str] = Query(
        ["donation.created_at:desc"],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int = Query(
        50,
        description="Maximum number of results to return.",
        le=100,
        ge=1,
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
):
    """
    Get donations for a specific account.
    """

    try:
        return _get_donations(
            accounts=[account],
            donors=donors,
            start_time=start_time,
            end_time=end_time,
            sort=sort,
            limit=limit,
            offset=offset,
            currency=currency,
        )
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/donors", response_model=CampaignStats)
def get_accounts_donors(
    accounts: list[str] = Query(
        [],
        description="Filter by account URLs or FQDNs. Wildcards are supported.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    group_by: list[str] = Query(
        [],
        description=(
            'Fields to group by (e.g., "account.url", "donation.donor"). '
            'Date units are also supported (e.g., "donation.created_at:day", '
            '"donation.created_at:week", "donation.created_at:month", '
            '"donation.created_at:year").'
        ),
    ),
    sort: list[str] = Query(
        [],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int = Query(
        50,
        description="Maximum number of results to return.",
        ge=1,
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
):
    """
    Get campaigns stats by donors.
    """
    if not group_by:
        group_by = []
    if "donation.donor" not in group_by:
        group_by = ["donation.donor"] + list(group_by or [])

    try:
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
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/donations/rss", response_model=str)
def get_donations_feed(
    accounts: list[str] = Query(
        [],
        description="Filter by account URLs or FQDNs. Wildcards are supported.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    sort: list[str] = Query(
        ["donation.created_at:desc"],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int = Query(
        25,
        description="Maximum number of results to return.",
        le=100,
        ge=1,
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
) -> Response:
    """
    Get donations (RSS feed).
    """
    ctx = get_ctx()
    donations = _get_donations(
        accounts=accounts,
        donors=donors,
        start_time=start_time,
        end_time=end_time,
        sort=sort,
        limit=limit,
        offset=offset,
        currency=currency,
    )

    try:
        return Response(
            content=FeedsGenerator(ctx.config).generate_donations_feed(donations),
            media_type="application/rss+xml",
        )
    except PermissionError as e:
        return Response(content=str(e), status_code=403)


@router.get("/accounts/{account}/donations/rss", response_model=str)
def get_account_donations_feed(
    account: str = Path(
        ...,
        description="Account URLs or FQDNs.",
    ),
    donors: list[str] = Query(
        [],
        description="Filter by donor names. Wildcards are supported.",
    ),
    start_time: str | None = Query(
        None,
        description="Filter donations created after this time (ISO 8601 format).",
    ),
    end_time: str | None = Query(
        None,
        description="Filter donations created before this time (ISO 8601 format).",
    ),
    sort: list[str] = Query(
        ["donation.created_at:desc"],
        description=(
            'Fields to sort by (e.g., "amount", "donation.created_at"). '
            'Add ":desc" for descending order.'
        ),
    ),
    limit: int = Query(
        25,
        description="Maximum number of results to return.",
        le=100,
        ge=1,
    ),
    offset: int | None = Query(
        None,
        description="Number of results to skip before starting to collect the result set.",
    ),
    currency: str | None = Query(
        None,
        description="Currency code for amounts (default: USD).",
    ),
) -> Response:
    """
    Get donations for a specific account (RSS feed).
    """
    ctx = get_ctx()

    try:
        donations = _get_donations(
            accounts=[account],
            donors=donors,
            start_time=start_time,
            end_time=end_time,
            sort=sort,
            limit=limit,
            offset=offset,
            currency=currency,
        )
    except PermissionError as e:
        return Response(content=str(e), status_code=403)

    return Response(
        content=FeedsGenerator(ctx.config).generate_donations_feed(donations),
        media_type="application/rss+xml",
    )
