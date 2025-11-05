from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from logging import getLogger
from threading import RLock
from typing import Iterator, Any

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from ..model import (
    Account,
    ApiSortType,
    Campaign,
    CampaignAccountStats,
    CampaignDonationInfo,
    CampaignStats,
    CampaignStatsAmount,
)
from ._model import (
    Account as DbAccount,
    Campaign as DbCampaign,
    CampaignDonation as DbCampaignDonation,
)

log = getLogger(__name__)


class Campaigns(ABC):
    """
    Database interface for campaigns.
    """

    _write_lock: RLock
    _table_by_search_key: dict[str, type[DbCampaign]] = {
        "account": DbAccount,
        "campaign": DbCampaign,
        "donation": DbCampaignDonation,
    }

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    @abstractmethod
    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> dict: ...

    def get_campaign(self, campaign_url: str) -> Campaign | None:
        with self.get_session() as session:
            campaign = (
                session.query(DbCampaign)
                .filter(DbCampaign.url == campaign_url)  # type: ignore
                .first()
            )

            if campaign:
                donations = list(campaign.donations)
                donations.sort(key=lambda d: d.created_at, reverse=True)

            return campaign.to_model() if campaign else None

    @classmethod
    def _params_to_columns(cls, params: list[str]) -> dict[str, Any]:
        columns = {}
        for param in params:
            param = param.lower().strip()
            field_tokens = param.split(".")
            table = cls._table_by_search_key.get(field_tokens[0])
            assert table, (
                f"Invalid group_by field table: {param}. "
                "Supported tables are: {list(Campaigns._table_by_search_key.keys())}"
            )
            attr = field_tokens[1] if len(field_tokens) > 1 else None
            assert attr, f"Invalid group_by field attribute: {param}."

            # Split time-based grouping (e.g., created_at:day)
            attr_tokens = attr.split(":")
            attr = attr_tokens[0]
            time_unit = attr_tokens[1] if len(attr_tokens) > 1 else None
            if time_unit:
                time_unit = time_unit.lower()
                if time_unit == "day":
                    column = func.strftime("%Y-%m-%d", getattr(table, attr)).label(
                        "day"
                    )
                elif time_unit == "week":
                    column = func.date(
                        getattr(table, attr), "weekday 1", "-6 days"
                    ).label("week")
                elif time_unit == "month":
                    column = func.strftime("%Y-%m", getattr(table, attr)).label("month")
                elif time_unit == "year":
                    column = func.strftime("%Y", getattr(table, attr)).label("year")
                else:
                    raise AssertionError(
                        f"Invalid time unit in group_by field: {param}."
                    )
            else:
                column = getattr(table, attr, None)

            assert column is not None, f"Invalid group_by field: {param}."
            columns[param] = column

        return columns

    def get_campaigns(
        self,
        accounts: list[str] | None = None,
        donors: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        group_by: list[str] | None = None,
        sort: list[tuple[str, ApiSortType]] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        currency: str | None = None,
    ) -> CampaignStats:
        with self.get_session() as session:
            group_columns = {}
            if group_by:
                group_columns = self._params_to_columns(group_by)
            if not group_columns:
                group_columns = {"campaign.url": DbCampaign.url}

            output = [
                *[
                    (DbAccount if group_column == DbAccount.url else group_column)
                    for group_column in group_columns.values()
                ],
                func.sum(DbCampaignDonation.amount).label("amount"),
                func.min(DbCampaignDonation.created_at).label("first_donation_time"),
                func.max(DbCampaignDonation.created_at).label("last_donation_time"),
            ]

            query = (
                session.query(*output)
                .join(DbCampaign.account)
                .outerjoin(DbCampaign.donations)
            )

            if accounts:
                query = query.filter(
                    DbAccount.url.in_([Account.to_url(account) for account in accounts])
                )
            if donors:
                query = query.filter(DbCampaignDonation.donor.in_(donors))
            if start_time:
                query = query.filter(DbCampaignDonation.created_at >= start_time)
            if end_time:
                query = query.filter(DbCampaignDonation.created_at <= end_time)

            query = query.group_by(*group_columns.values())
            query = self._apply_sort(query, sort or [("amount", ApiSortType.DESC)])

            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            records = query.all()
            return self._records_to_stats(
                records,
                group_columns=group_columns,
                currency=currency,
            )

    def get_donations(
        self,
        accounts: list[str] | None = None,
        donors: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sort: list[tuple[str, ApiSortType]] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        currency: str | None = None,
    ) -> list[CampaignDonationInfo]:
        with self.get_session() as session:
            query = (
                session.query(DbAccount, DbCampaign, DbCampaignDonation)
                .join(DbCampaignDonation.campaign)
                .join(DbCampaign.account)
            )

            if accounts:
                query = query.filter(
                    DbAccount.url.in_([Account.to_url(account) for account in accounts])
                )
            if donors:
                query = query.filter(DbCampaignDonation.donor.in_(donors))
            if start_time:
                query = query.filter(DbCampaignDonation.created_at >= start_time)
            if end_time:
                query = query.filter(DbCampaignDonation.created_at <= end_time)

            query = self._apply_sort(query, sort or [("created_at", ApiSortType.DESC)])

            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            return [
                CampaignDonationInfo(
                    id=donation.id,
                    account=account.to_model(),
                    campaign_url=campaign.url,
                    amount=CampaignStatsAmount(
                        amount=self.convert(
                            donation.amount,
                            from_currency="USD",
                            to_currency=currency or "USD",
                            date=None,  # Use current rate for simplicity
                        )["converted_amount"],
                        currency=currency or "USD",
                    ),
                    donor=donation.donor,
                    created_at=donation.created_at,
                )
                for account, campaign, donation in query.all()
            ]

    def _records_to_stats(
        self,
        records: list[tuple[Any, ...]],
        group_columns: dict[str, Any] | None = None,
        currency: str | None = None,
    ) -> CampaignStats:
        nested_dict = lambda: defaultdict(nested_dict)
        data = defaultdict(nested_dict)

        for record in records:
            amount, first_donation_time, last_donation_time = record[-3:]
            columns = record[:-3]
            group_key = []
            group_value = []
            data_node = data

            for i, (group_field, group_column) in enumerate(group_columns.items()):
                account = None
                value = columns[i]

                if group_field == "account.url":
                    group_key.append(group_field)
                    group_value.append(str(value.url))
                    account = value
                else:
                    group_key.append(group_field)
                    group_value.append(value)

                data_node = data_node[group_value[-1]]
                data_node["group_key"] = list(group_key)  # type: ignore
                data_node["group_value"] = list(group_value)  # type: ignore
                if account:
                    data_node["account"] = account.to_model()

                if i == len(group_columns) - 1:
                    data_node["amount"] = CampaignStatsAmount(
                        amount=self.convert(
                            amount or 0.0,
                            from_currency="USD",
                            to_currency=currency or "USD",
                            date=None,  # Use current rate for simplicity
                        )["converted_amount"],
                        currency=currency or "USD",
                    )
                    data_node["first_donation_time"] = first_donation_time
                    data_node["last_donation_time"] = last_donation_time

        return self._data_to_stats(data)

    @classmethod
    def _data_to_stats(cls, data_node: dict) -> CampaignStats:
        args = {
            "group_key": data_node.get("group_key", []),
            "group_value": data_node.get("group_value", []),
            "data": [],
        }

        for key, value in data_node.items():
            if key in (
                "group_key",
                "group_value",
                "account",
                "amount",
                "first_donation_time",
                "last_donation_time",
            ):
                args[key] = value
            else:
                args["data"].append(cls._data_to_stats(value))

        stats_cls = CampaignAccountStats if data_node.get("account") else CampaignStats
        return stats_cls(**args)

    @classmethod
    def _apply_sort(cls, query: Query, sort: list[tuple[str, ApiSortType]]) -> Query:
        group_sort_columns = {
            "amount": func.sum(DbCampaignDonation.amount),
            "first_donation_time": func.min(DbCampaignDonation.created_at),
            "last_donation_time": func.max(DbCampaignDonation.created_at),
        }

        table_sort_columns_str = [
            column for column, _ in sort if column not in group_sort_columns
        ]

        table_sort_columns = cls._params_to_columns(table_sort_columns_str)

        for sort_field, sort_type in sort:
            sort_column = group_sort_columns.get(sort_field)
            if sort_column is None:
                sort_column = table_sort_columns.get(sort_field)
                assert sort_column, f"Invalid sort field: {sort_field}."

            sort_column = (
                sort_column.asc()
                if sort_type == ApiSortType.ASC
                else sort_column.desc()
            )
            query = query.order_by(sort_column)

        return query

    def save_campaigns(self, campaigns: list[Campaign]):
        with self._write_lock, self.get_session() as session:
            db_campaigns: dict[str, Campaign] = {  # type: ignore
                str(db_campaign.url): db_campaign
                for db_campaign in (
                    session.query(DbCampaign)
                    .filter(
                        DbCampaign.url.in_([campaign.url for campaign in campaigns])
                    )
                    .all()
                )
            }

            for campaign in campaigns:
                db_campaign = db_campaigns.get(campaign.url)
                if not db_campaign:
                    log.info(
                        "Adding new campaign with %d donations: %s",
                        len(campaign.donations),
                        campaign.url,
                    )
                    session.add(DbCampaign.from_model(campaign))

                    for donation in campaign.donations:
                        session.add(DbCampaignDonation.from_model(donation))
                elif db_campaign.donations_cursor != campaign.donations_cursor:
                    existing_donations = {
                        donation.id for donation in db_campaign.donations
                    }
                    new_donations = [
                        donation
                        for donation in campaign.donations
                        if donation.id not in existing_donations
                    ]

                    db_campaign.donations_cursor = campaign.donations_cursor
                    if new_donations:
                        log.info(
                            "Added %d donations to campaign: %s",
                            len(new_donations),
                            campaign.url,
                        )

                        for donation in new_donations:
                            session.add(DbCampaignDonation.from_model(donation))

            session.commit()
