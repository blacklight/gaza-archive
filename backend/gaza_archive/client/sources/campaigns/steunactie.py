import logging
import re
from datetime import datetime, timedelta, timezone
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup

from ....model.campaign import Campaign, CampaignDonation
from ._source import CampaignSource

log = logging.getLogger(__name__)


class SteunactieCampaignSource(
    CampaignSource
):  # pylint: disable=too-few-public-methods
    """
    Configuration for steunactie.nl campaigns.
    """

    _api_url_pattern = (
        "https://steunactie.nl/donations/all/{campaign_id}/0/latest/1/?page={page}"
    )

    @property
    def url_pattern(self) -> re.Pattern:
        return re.compile(r"^https://(www\.)?steunactie\.nl/fundraiser/([^/?#&]+).*$")

    def parse_url(self, url: str) -> str | None:
        match = self.url_pattern.match(url)
        if match:
            return f"https://steunactie.nl/fundraiser/{match.group(2)}"

        return None

    def _get_campaign_id(self, campaign_url: str):
        response = requests.head(
            campaign_url,
            timeout=self.config.http_timeout,
            headers={
                "User-Agent": self.config.user_agent,
            },
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            log.warning(
                "Cannot fetch ID for campaign %s: %s: %s",
                campaign_url,
                response.status_code,
                e,
            )
            return None

        location = response.headers.get("Location", "")
        match = re.search(r".*/-([0-9]+)(\?.*)*", location)
        if not match:
            log.warning("Could not parse ID for campaign %s", campaign_url)
            return None

        campaign_id = match.group(1)
        log.debug("Scraped campaign ID for %s: %s", campaign_url, campaign_id)
        return campaign_id

    @staticmethod
    def _parse_date(text: str) -> datetime | None:
        text = text.strip().replace("op ", "") if text else ""
        try:
            return datetime.strptime(text, "%d-%m-%Y").replace(tzinfo=timezone.utc)
        except ValueError:
            # In this case, it's a date in the format "<w> week/weken, <d> dag/dagen, <u> uur/uren geleden"
            regex = re.compile(
                r"(?:(?P<weeks>\d+)\s+(week|weken)?[, ]*)?(?:(?P<days>\d+)\s+dag(?:en)?[, ]*)?"
                r"(?:(?P<hours>\d+)\s+uur(?:en)?)?\s+geleden"
            )

            match = regex.match(text)
            if not match:
                return None

            weeks = int(match.group("weeks") or 0)
            days = int(match.group("days") or 0)
            hours = int(match.group("hours") or 0)
            return datetime.now(timezone.utc) - timedelta(weeks=weeks, days=days, hours=hours)

    def fetch_donations(self, campaign: Campaign) -> Campaign:
        campaign_id = self._get_campaign_id(campaign.url)
        if not campaign_id:
            return campaign

        page = 1
        donations = []
        current_cursor = campaign.donations_cursor
        all_new_donations_fetched = False

        while True:
            log.debug("Fetching donations from %s (page=%d)", campaign.url, page)

            response = requests.get(
                self._api_url_pattern.format(campaign_id=campaign_id, page=page),
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )

            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                if response.status_code == 429:
                    sleep_seconds = int(response.headers.get("Retry-After", "10")) + 1
                    log.warning(
                        "Rate limit exceeded for %s, sleeping for %d seconds...",
                        campaign.url,
                        sleep_seconds,
                    )
                    sleep(sleep_seconds)
                    continue

                log.error(
                    "HTTP error %d fetching donations from %s: %s",
                    response.status_code,
                    campaign.url,
                    e,
                )
                break

            # Example HTML item structure:
            #     <li class="list-group-item flex-column align-items-start">
            #         <div class="d-flex w-100 justify-content-between">
            #             <span>Anoniem</span>
            #             <strong class="amount">€ 25,00</strong>
            #         </div>
            #         <small class="date float-right">
            #             op 18-09-2025
            #         </small>
            #     </li>

            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            donation_items = soup.find_all("li", class_="list-group-item")
            if not donation_items:
                break  # No more donations to fetch

            for item in donation_items:
                name_tag = None
                name_div = item.find("div", class_="d-flex")
                if name_div:
                    name_tag = name_div.find("span")

                amount_tag = item.find("strong", class_="amount")
                date_tag = item.find("small", class_="date")

                donor_name = name_tag.text.strip() if name_tag else None
                if donor_name == "Anoniem":
                    donor_name = None

                amount_text = amount_tag.text.strip() if amount_tag else "€ 0,00"
                date_text = date_tag.text.strip().replace("op ", "") if date_tag else ""

                # Parse date
                donation_date = self._parse_date(date_text)
                if not donation_date:
                    log.warning(
                        "Could not parse donation date '%s' for campaign %s",
                        date_text,
                        campaign.url,
                    )
                    continue

                # Parse amount
                amount_value = float(
                    amount_text.replace("€", "").replace(",", ".").strip()
                )

                amount = self.db.convert(
                    amount=amount_value,
                    from_currency="EUR",
                    to_currency="USD",
                    date=donation_date.date().isoformat(),
                )["converted_amount"]

                # Generate a donation ID based on donation datetime and a random component,
                # in lack of better identifiers.
                donation_id = int(f"{donation_date.strftime('%Y%m%d%H')}{randint(1000, 9999)}")
                donation_cursor = int(donation_date.strftime('%Y%m%d%H'))
                if donation_cursor < int(current_cursor or 0):
                    all_new_donations_fetched = True
                    break  # We have reached already fetched donations

                donations.append(
                    CampaignDonation(
                        id=str(donation_id),
                        url=f"{campaign.url}#donation-{donation_id}",
                        campaign_url=campaign.url,
                        donor=donor_name,
                        amount=amount,
                        created_at=donation_date,
                    )
                )

            if not donations or all_new_donations_fetched:
                break

            page += 1

        campaign.donations = donations
        campaign.donations_cursor = str(
            max(
                *[int(donation.created_at.strftime('%Y%m%d%H')) for donation in donations],
                int(current_cursor or 0),
            )
        )

        return campaign
