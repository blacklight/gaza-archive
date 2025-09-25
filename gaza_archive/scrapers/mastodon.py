from abc import ABC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger

import requests

from ..config import Config
from ..errors import AccountNotFoundError, HttpError
from ..model import Account

log = getLogger(__name__)


class MastodonApi(ABC):
    """
    Mastodon API facade.
    """

    config: Config

    def _http_get(self, url: str, *args, **kwargs) -> dict:
        """
        Perform a GET request to the Mastodon API.
        """
        response = requests.get(
            url,
            *args,
            timeout=kwargs.pop("timeout", self.config.http_timeout),
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
                **kwargs.pop("headers", {}),
            },
            **kwargs,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise HttpError(
                f"HTTP error {response.status_code} for {url}",
                status_code=response.status_code,
                exception=exc,
            ) from exc

        return response.json()

    def _get_account_id(self, account: Account) -> str:
        """
        Get the Mastodon ID of an account.
        """
        if not account.id:
            try:
                account_info = self._http_get(
                    f"{account.instanceApiUrl}/accounts/lookup",
                    params={"acct": account.username},
                )
            except HttpError as exc:
                if exc.status_code == 404:
                    raise AccountNotFoundError(
                        f"Account {account.username} not found on {account.instance}",
                        account=account.username,
                    ) from exc

                raise

            account.id = str(account_info["id"])

        return account.id

    def refresh_account(self, account: Account) -> Account:
        """
        Get the Mastodon ID of an account.
        """
        try:
            if not account.id:
                account.id = self._get_account_id(account)
        except AccountNotFoundError as exc:
            if not account.disabled:
                log.warning(str(exc))

            account.disabled = True
            return account

        account_info = self._http_get(account.apiURL)
        account.id = str(account_info["id"])
        account.display_name = account_info.get("display_name") or account.username
        account.avatar_url = account_info.get("avatar_static")
        account.header_url = account_info.get("header_static")
        account.profile_note = account_info.get("note")
        account.created_at = datetime.fromisoformat(account_info["created_at"])
        if account_info.get("locked"):
            account.disabled = account_info["locked"]

        log.info("Refreshed account: %s", account.url)
        return account

    def refresh_accounts(self, accounts: list[Account]) -> list[Account]:
        """
        Refresh multiple accounts concurrently.
        """
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            refreshed_accounts = list(executor.map(self.refresh_account, accounts))

        return refreshed_accounts
