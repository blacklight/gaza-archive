from abc import ABC, abstractmethod
from contextlib import contextmanager
from logging import getLogger
from threading import RLock
from typing import Iterator

from sqlalchemy.orm import Session

from ..model import Campaign
from ._model import (
    Campaign as DbCampaign,
    CampaignDonation as DbCampaignDonation,
)

log = getLogger(__name__)


class Campaigns(ABC):
    """
    Database interface for campaigns.
    """

    _write_lock: RLock

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def get_campaign(self, campaign_url: str) -> Campaign | None:
        with self.get_session() as session:
            campaign = session.query(DbCampaign).filter(DbCampaign.url == campaign_url).first()
            if campaign:
                donations = list(campaign.donations)
                donations.sort(key=lambda d: d.created_at, reverse=True)

            return campaign.to_model() if campaign else None

    def save_campaigns(self, campaigns: list[Campaign]):
        with self._write_lock, self.get_session() as session:
            db_campaigns: dict[str, Campaign] = {
                str(db_campaign.url): db_campaign
                for db_campaign in (
                    session.query(DbCampaign)
                    .filter(DbCampaign.url.in_([campaign.url for campaign in campaigns]))
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
                    existing_donations = {donation.id for donation in db_campaign.donations}
                    new_donations = [
                        donation
                        for donation in campaign.donations
                        if donation.id not in existing_donations
                    ]

                    log.info(
                        "Added %d donations to campaign: %s",
                        len(new_donations),
                        campaign.url,
                    )

                    db_campaign.donations_cursor = campaign.donations_cursor
                    for donation in new_donations:
                        session.add(DbCampaignDonation.from_model(donation))

            session.commit()
