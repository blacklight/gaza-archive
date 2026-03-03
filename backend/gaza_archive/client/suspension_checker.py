import re
import time
from abc import ABC
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import List, Dict

import requests

from ..config import Config
from ..errors import HttpError
from ..model import Account
from ..model.suspension import SuspensionState

log = getLogger(__name__)


@dataclass
class Server:
    """Represents a Mastodon server for state checking."""

    domain: str
    mau: int = 0

    @property
    def url(self) -> str:
        if self.domain.startswith("https://") or self.domain.startswith("http://"):
            return self.domain.rstrip("/")
        return f"https://{self.domain.rstrip('/')}"

    @property
    def search_api_url(self) -> str:
        return f"{self.url}/api/v2/search"


class ServerLoader:
    """Loads Mastodon servers from fedidb API."""

    def __init__(self, config: Config):
        self.config = config

    def load_servers(
        self, custom_servers: list[str] | None = None, limit: int = 50
    ) -> list[Server]:
        """
        Load servers from fedidb API or use custom list.
        Follows pattern from /home/blacklight/git_tree/dotfiles/bin/mastodon-block-checker
        """
        if custom_servers:
            return [
                Server(domain=re.sub(r"https?://", "", s).rstrip("/"))
                for s in custom_servers
                if s.strip()
            ]

        results = {}
        next_url = "https://api.fedidb.org/v1.1/servers"
        log.info("Fetching up to %d Mastodon servers from Fedidb...", limit)

        while next_url and len(results) < limit:
            response = requests.get(
                next_url,
                timeout=self.config.http_timeout,
                headers={"User-Agent": self.config.user_agent},
                params={
                    "limit": 50,
                    "sort": "mau-desc",
                },
            )

            response.raise_for_status()
            data = response.json()
            next_url = data.get("links", {}).get("next")

            for item in data.get("data", []):
                if len(results) >= limit:
                    break

                # Limit to Mastodon servers only
                if item.get("software", {}).get("name") == "Mastodon":
                    results[item["domain"]] = Server(
                        domain=item["domain"],
                        mau=item.get("stats", {}).get("monthly_active_users", 0),
                    )

            log.debug("Fetched %d/%d servers...", len(results), limit)

        log.info("Loaded %d servers from Fedidb", len(results))
        return list(results.values())


class SuspensionStateChecker(ABC):
    """
    Mixin for checking account suspension states across Mastodon servers.
    Follows patterns from other bot mixins in the codebase.
    """

    config: Config
    _server_loader: ServerLoader | None = None

    @property
    def server_loader(self) -> ServerLoader:
        """Lazy-initialized server loader."""
        if self._server_loader is None:
            self._server_loader = ServerLoader(self.config)
        return self._server_loader

    def _http_get(self, url: str, **kwargs) -> dict:
        """
        HTTP GET with rate limiting handling.
        Follows exact pattern from mastodon.py
        """
        while True:
            response = requests.get(
                url,
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
                return response.json()
            except requests.ConnectionError as exc:
                raise HttpError(
                    f"Connection error for {url}",
                    exception=exc,
                ) from exc
            except requests.HTTPError as exc:
                if response.status_code == 429:
                    rate_limit_reset_date = response.headers.get("X-RateLimit-Reset")
                    if rate_limit_reset_date:
                        reset_timestamp = datetime.fromisoformat(
                            re.sub(r"Z$", "+00:00", rate_limit_reset_date)
                        ).timestamp()
                    else:
                        reset_timestamp = datetime.now().timestamp() + 10

                    sleep_seconds = int(
                        max(20.0, reset_timestamp - datetime.now().timestamp()) + 1
                    )
                    log.warning(
                        "Rate limit exceeded for %s, sleeping for %d seconds...",
                        url,
                        sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
                else:
                    raise HttpError(
                        f"HTTP error {response.status_code} for {url}",
                        status_code=response.status_code,
                        exception=exc,
                    ) from exc

    def check_account_on_server(
        self, account_fqn: str, server: Server
    ) -> tuple[str, SuspensionState] | None:
        """Check account state on a specific server."""
        try:
            data = self._http_get(
                server.search_api_url,
                params={"q": account_fqn, "type": "accounts", "limit": 1},
            )

            accounts = data.get("accounts", [])
            if not accounts:
                return (server.url, SuspensionState.DELETED)

            account = accounts[0]
            if account.get("suspended", False):
                state = SuspensionState.SUSPENDED
            elif account.get("limited", False):
                state = SuspensionState.LIMITED
            else:
                state = SuspensionState.ACTIVE

            return (server.url, state)

        except Exception as e:
            log.warning("Error checking %s on %s: %s", account_fqn, server.domain, e)
            return None

    def refresh_suspension_states(
        self, accounts: List[Account]
    ) -> Dict[str, Dict[str, SuspensionState]]:
        """
        Refresh suspension states for all accounts across servers.
        Uses ThreadPoolExecutor pattern from mastodon.py
        """
        # Load servers (custom or top 50 from fedidb)
        servers = self.server_loader.load_servers(
            custom_servers=self.config.account_state_custom_servers,
            limit=self.config.account_state_servers_limit,
        )

        # Always include parent instances
        account_instances = {
            acc.instance_url.replace("https://", "") for acc in accounts
        }
        parent_servers = [Server(domain=instance) for instance in account_instances]
        all_servers = list(
            {server.domain: server for server in (servers + parent_servers)}.values()
        )

        log.info(
            "Checking %d accounts against %d servers...",
            len(accounts),
            len(all_servers),
        )

        results = {}

        with ThreadPoolExecutor(
            max_workers=self.config.account_state_check_workers
        ) as executor:
            # Submit all account/server combinations
            future_to_lookup = {
                executor.submit(self.check_account_on_server, account.fqn, server): (
                    account,
                    server,
                )
                for account in accounts
                for server in all_servers
            }

            # Collect results using as_completed pattern
            for future in as_completed(future_to_lookup):
                account, server = future_to_lookup[future]
                try:
                    result = future.result()
                    if result:
                        server_url, state = result
                        if account.url not in results:
                            results[account.url] = {}
                        results[account.url][server_url] = state
                except Exception as e:
                    log.error(
                        "Error processing %s on %s: %s", account.fqn, server.domain, e
                    )

        log.info("Completed suspension state check for %d accounts", len(results))
        return results
