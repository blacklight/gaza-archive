from datetime import datetime, timezone

from fastapi import APIRouter

from ...db._model import (
    Account as DbAccount,
    Campaign as DbCampaign,
    CampaignDonation as DbCampaignDonation,
)

from .._ctx import get_ctx

router = APIRouter(
    prefix="/api/v1/internal",
    tags=["internal"],
    include_in_schema=False,
)


@router.get("/db_fields")
def get_db_fields() -> dict[str, str]:
    """
    Get list of database fields for campaigns allowed for filter/sort/group_by.

    :return: List of database fields, as a `field` -> `type` mapping.
    """
    # Inspect the account, campaign and donation tables for their fields
    db_fields = {}
    for model, prefix in [
        (DbAccount, "account."),
        (DbCampaign, "campaign."),
        (DbCampaignDonation, "donation."),
    ]:
        for field, column in sorted(
            model.__table__.columns.items(),
            key=lambda entry: entry[0],
        ):
            db_fields[f"{prefix}{field}"] = str(column.type)

    return db_fields


@router.get("/currencies")
def get_supported_currencies() -> list[str]:
    """
    Get list of supported currencies for exchange rates.

    :return: List of supported currency codes.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    latest_rates = get_ctx().db.get_rates(date=today)
    return sorted(latest_rates.keys()) if latest_rates else []