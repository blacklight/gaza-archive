from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from logging import getLogger
from time import sleep
from typing import Iterator

import requests
from sqlalchemy.orm import Session

from ..config import Config
from ..db._model import ExchangeRate

log = getLogger(__name__)


class CurrencyConverter(ABC):
    """
    A currency conversion API that fetches and caches exchange rates.
    Supports historical rates and on-the-fly conversion.
    """

    base_currency = "USD"
    base_url = "https://api.exchangerate-api.com/v4"
    backup_url = "https://data.fixer.io/api"
    cache_max_age_hours: int = 24
    config: Config
    _cached_rates: dict[str, dict] = {}

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def _get_from_cache(self, date: str) -> dict | None:
        """Retrieve rates from cache if available and valid."""
        # First check in-memory cache
        if date in self._cached_rates:
            return self._cached_rates[date]

        with self.get_session() as session:
            cache_entry = (
                session.query(ExchangeRate)
                .filter(ExchangeRate.date == date)  # type: ignore[attr-defined]
                .first()
            )

            if cache_entry:
                self._cached_rates[date] = cache_entry.rates
                return cache_entry.rates

        return None

    def _save_to_cache(self, date: str, rates: dict):
        """Save rates to cache using SQLAlchemy ORM."""
        self._cached_rates[date] = rates

        with self.get_session() as session:
            # Check if entry already exists
            existing = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.date == date,  # type: ignore[attr-defined]
                )
                .first()
            )

            if existing:
                # Update existing entry
                existing.rates = rates
            else:
                # Create new entry
                new_entry = ExchangeRate(date, rates)
                session.add(new_entry)
                session.commit()

    def _fetch_rates_from_api(self, date: str, use_backup: bool = True) -> dict:
        """Fetch exchange rates from external API."""
        try:
            # Try primary API (exchangerate-api.com)
            if date == datetime.now().strftime("%Y-%m-%d"):
                # Current rates
                url = f"{self.base_url}/latest/{self.base_currency}"
            else:
                # Historical rates
                url = (
                    f"https://v6.exchangerate-api.com/v6/{self.config.exchange_rates_api_key or ''}"
                    f"/history/{self.base_currency}/{'/'.join(date.split('-'))}"
                )

            response = requests.get(
                url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )

            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                try:
                    error_type = response.json().get("error-type", "")
                except Exception as e2:
                    log.debug("Failed to parse error response: %s", e2)
                    error_type = "Unknown error"

                raise RuntimeError(f"API Error: {error_type}") from e

            data = response.json()
            return data.get("rates", {})
        except Exception as e:
            if use_backup:
                log.debug(
                    "Primary currency API failed (%s), falling back to backup API",
                    e,
                )

                try:
                    return self._fetch_from_backup_api(date)
                except Exception as backup_e:
                    log.warning(
                        "Backup currency API failed: %s. Falling back to most recent rates",
                        backup_e
                    )

                    return self._fetch_rates_from_api(
                        datetime.now().strftime("%Y-%m-%d"),
                        use_backup=False,
                    )

            raise RuntimeError(f"Failed to fetch rates: {e}") from e

    def _fetch_from_backup_api(self, date: str) -> dict:
        """Fetch from backup API (fixer.io) - requires API key."""
        if not self.config.fixer_io_api_key:
            raise ValueError("No API key provided for backup service")

        try:
            while True:
                url = f"{self.backup_url}/{date}"
                params = {"access_key": self.config.fixer_io_api_key}

                response = requests.get(url, params=params, timeout=self.config.http_timeout)
                try:
                    response.raise_for_status()
                    break
                except requests.HTTPError as e:
                    try:
                        error_info = response.json().get("error", {}).get("type", "")
                    except Exception as e2:
                        log.debug("Failed to parse backup API error response: %s", e2)
                        error_info = "Unknown error"

                    if response.status_code == 429:
                        log.warning(
                            "Backup API rate limit exceeded. Consider upgrading your plan. "
                            "Waiting 30 seconds before retrying..."
                        )
                        sleep(30.)
                    else:
                        raise RuntimeError(f"Backup API HTTP error: {response.status_code}: {error_info}") from e

            data = response.json()

            if data.get("success"):
                api_base_currency = data.get("base", "EUR")
                rates = data.get("rates", {})
                if api_base_currency != self.base_currency:
                    base_rate = rates[self.base_currency]
                    adjusted_rates = {
                        currency: rate / base_rate for currency, rate in rates.items()
                    }
                    return adjusted_rates

                return rates

            raise RuntimeError(
                f"API Error: {data.get('error', {}).get('info', 'Unknown error')}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch rates: {e}") from e

    def get_rates(self, date: str, force_refresh: bool = False) -> dict:
        """
        Get exchange rates for a specific date and base currency.

        :param date: Date in YYYY-MM-DD format
        :param force_refresh: Force fetch from API instead of cache
        :return: Dictionary of exchange rates
        """
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("Date must be in YYYY-MM-DD format") from e

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_rates = self._get_from_cache(date)
            if cached_rates:
                return cached_rates

        # Fetch from API
        log.debug("Fetching exchange rates for %s", date)
        rates = self._fetch_rates_from_api(date)

        # Cache the results
        self._save_to_cache(date, rates)
        return rates

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> dict:
        """
        Convert amount from one currency to another.

        :param amount: Amount to convert
        :param from_currency: Source currency code
        :param to_currency: Target currency code
        :param date: Date for conversion (default: today)
        :return: Dictionary with conversion details
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Get USD->* rates for the date
        usd_rates = self.get_rates(date)

        if to_currency not in usd_rates:
            raise ValueError(f"Currency {to_currency} not found in rates for {date}")

        # If from_currency is not USD, convert amount to USD first
        if from_currency != self.base_currency:
            if from_currency not in usd_rates:
                raise ValueError(f"Currency {from_currency} not found in rates for {date}")

            amount /= usd_rates[from_currency]

        # Perform conversion
        exchange_rate = usd_rates[to_currency]
        converted_amount = amount * exchange_rate

        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": exchange_rate,
            "converted_amount": round(converted_amount, 2),
            "date": date,
        }
