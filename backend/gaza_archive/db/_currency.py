from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Iterator, List

import requests
from sqlalchemy.orm import Session

from ..config import Config
from ..db._model import CurrencyPair, ExchangeRate

log = getLogger(__name__)


class CurrencyConverter(ABC):
    """
    A currency conversion API that fetches and caches exchange rates.
    Supports historical rates and on-the-fly conversion.
    """

    base_url = "https://api.exchangerate-api.com/v4"
    backup_url = "https://api.fixer.io/v1"
    cache_max_age_hours: int = 24
    config: Config

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]: ...

    def _get_from_cache(self, date: str, base_currency: str) -> dict | None:
        """Retrieve rates from cache if available and valid."""
        with self.get_session() as session:
            cache_entry = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.date == date,  # type: ignore[attr-defined]
                    ExchangeRate.base_currency == base_currency,  # type: ignore[attr-defined]
                )
                .first()
            )

            if cache_entry and not cache_entry.is_expired(self.cache_max_age_hours):
                return cache_entry.rates
            if cache_entry and cache_entry.is_expired(self.cache_max_age_hours):
                # Remove expired entry
                session.delete(cache_entry)
                session.commit()

        return None

    def _save_to_cache(self, date: str, base_currency: str, rates: dict):
        """Save rates to cache using SQLAlchemy ORM."""
        with self.get_session() as session:
            # Check if entry already exists
            existing = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.date == date,  # type: ignore[attr-defined]
                    ExchangeRate.base_currency == base_currency,  # type: ignore[attr-defined]
                )
                .first()
            )

            if existing:
                # Update existing entry
                existing.rates = rates
            else:
                # Create new entry
                new_entry = ExchangeRate(date, base_currency, rates)
                session.add(new_entry)
                session.commit()

    def _track_currency_pair_usage(self, from_currency: str, to_currency: str):
        """Track usage of currency pairs for analytics."""
        with self.get_session() as session:
            pair = (
                session.query(CurrencyPair)
                .filter(
                    CurrencyPair.from_currency == from_currency,  # type: ignore[attr-defined]
                    CurrencyPair.to_currency == to_currency,  # type: ignore[attr-defined]
                )
                .first()
            )

            if pair:
                pair.increment_usage()
            else:
                new_pair = CurrencyPair(from_currency, to_currency)
                session.add(new_pair)

    def _fetch_rates_from_api(self, date: str, base_currency: str = "USD") -> dict:
        """Fetch exchange rates from external API."""
        try:
            # Try primary API (exchangerate-api.com)
            if date == datetime.now().strftime("%Y-%m-%d"):
                # Current rates
                url = f"{self.base_url}/latest/{base_currency}"
            else:
                # Historical rates
                url = f"{self.base_url}/history/{base_currency}/{date}"

            response = requests.get(
                url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
            )
            response.raise_for_status()

            data = response.json()
            return data.get("rates", {})

        except requests.RequestException as e:
            log.warning(
                "Primary currency API failed (%s), falling back to backup API",
                e,
            )
            return self._fetch_from_backup_api(date, base_currency)

    def _fetch_from_backup_api(self, date: str, base_currency: str) -> dict:
        """Fetch from backup API (fixer.io) - requires API key."""
        if not self.config.fixer_io_api_key:
            raise ValueError("No API key provided for backup service")

        try:
            url = f"{self.backup_url}/{date}"
            params = {"access_key": self.config.fixer_io_api_key, "base": base_currency}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                return data.get("rates", {})

            raise RuntimeError(
                f"API Error: {data.get('error', {}).get('info', 'Unknown error')}"
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch rates: {e}") from e

    def get_rates(
        self, date: str, base_currency: str = "USD", force_refresh: bool = False
    ) -> dict:
        """
        Get exchange rates for a specific date and base currency.

        :param date: Date in YYYY-MM-DD format
        :param base_currency: Base currency code (default: USD)
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
            cached_rates = self._get_from_cache(date, base_currency)
            if cached_rates:
                return cached_rates

        # Fetch from API
        log.debug("Fetching exchange rates for %s with base %s", date, base_currency)
        rates = self._fetch_rates_from_api(date, base_currency)

        # Cache the results
        self._save_to_cache(date, base_currency, rates)
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

        # Track currency pair usage
        self._track_currency_pair_usage(from_currency, to_currency)

        # Get rates with base currency as from_currency
        rates = self.get_rates(date, from_currency)

        if to_currency not in rates:
            raise ValueError(f"Currency {to_currency} not found in rates for {date}")

        # Perform conversion
        exchange_rate = rates[to_currency]
        converted_amount = amount * exchange_rate

        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": exchange_rate,
            "converted_amount": round(converted_amount, 2),
            "date": date,
        }

    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        try:
            rates = self.get_rates(datetime.now().strftime("%Y-%m-%d"))
            return list(rates.keys())
        except Exception as e:
            # Return common currencies if API fails
            log.debug("Failed to fetch supported currencies: %s", e)
            return ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        with self.get_session() as session:
            total_entries = session.query(ExchangeRate).count()

            # Count expired entries
            expired_count = 0
            entries = session.query(ExchangeRate).all()
            for entry in entries:
                if entry.is_expired(self.cache_max_age_hours):
                    expired_count += 1

            # Get most used currency pairs
            top_pairs = (
                session.query(CurrencyPair)
                .order_by(CurrencyPair.usage_count.desc())
                .limit(10)
                .all()
            )

            return {
                "total_cached_entries": total_entries,
                "expired_entries": expired_count,
                "valid_entries": total_entries - expired_count,
                "top_currency_pairs": [
                    {
                        "pair": f"{pair.from_currency}/{pair.to_currency}",
                        "usage_count": pair.usage_count,
                        "last_used": pair.last_used.isoformat(),
                    }
                    for pair in top_pairs
                ],
            }

    def clear_cache(
        self, older_than_days: int | None = None, base_currency: str | None = None
    ):
        """Clear cache entries with optional filters."""
        with self.get_session() as session:
            query = session.query(ExchangeRate)

            if older_than_days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(
                    days=older_than_days
                )
                query = query.filter(ExchangeRate.updated_at < cutoff_date)  # type: ignore[attr-defined]

            if base_currency:
                query = query.filter(ExchangeRate.base_currency == base_currency)  # type: ignore[attr-defined]

            deleted_count = query.count()
            query.delete(synchronize_session=False)
            log.info("Cleared %d cache entries", deleted_count)

    def clear_expired_cache(self):
        """Remove all expired cache entries."""
        with self.get_session() as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=self.cache_max_age_hours
            )
            deleted = (
                session.query(ExchangeRate)
                .filter(ExchangeRate.updated_at < cutoff_time)  # type: ignore[attr-defined]
                .delete(synchronize_session=False)
            )

            log.info("Cleared %d expired cache entries", deleted)

    def get_cached_rates_by_date_range(
        self, start_date: str, end_date: str, base_currency: str = "USD"
    ) -> List[ExchangeRate]:
        """Get all cached rates within a date range."""
        with self.get_session() as session:
            return (  # type: ignore[return]
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.date >= start_date,  # type: ignore[attr-defined]
                    ExchangeRate.date <= end_date,  # type: ignore[attr-defined]
                    ExchangeRate.base_currency == base_currency,  # type: ignore[attr-defined]
                )
                .all()
            )
