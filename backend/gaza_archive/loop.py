import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Event, Thread
from time import time

from .client import Client
from .config import Config
from .db import Db
from .errors import AccountDeletedError, HttpError
from .model import Account, Campaign
from .model.suspension import SuspensionState
from .storages import FileStorage

log = logging.getLogger(__name__)
_client: Client | None = None


def _naive_utc(dt: datetime) -> datetime:
    """Return a naive UTC datetime, converting/removing tzinfo if present."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def get_client() -> Client | None:
    return _client


class Loop(Thread):
    """
    Main loop class.
    """

    def __init__(self, config: Config, db: Db, *args, **kwargs):
        global _client

        super().__init__(*args, **kwargs)
        self.db = db
        self.config = config
        self.storage = FileStorage(config)
        self.client = _client = Client(config=config, storage=self.storage, db=db)
        self._stop_event = Event()
        self._last_suspension_check = 0

    def _main(self):
        """
        Main loop
        """
        self.client.start_campaigns_bot()

        if not self.config.enable_crawlers:
            log.info("Crawlers are disabled. Exiting.")
            return

        while not self._stop_event.is_set():
            try:
                accounts = self.refresh_accounts()
                self.refresh_campaigns(accounts)
                self.refresh_suspensions(accounts)
            except Exception as e:
                log.error("Error in main loop: %s", e)
                log.exception(e)
            finally:
                self._stop_event.wait(self.config.poll_interval)

    def refresh_suspensions(self, accounts: list[Account]):
        # Check if it's time for suspension state refresh
        now = time()
        if not (
            self.config.account_state_check_enabled
            and now - self._last_suspension_check
            >= float(self.config.account_state_check_interval)
        ):
            return

        log.info("Refreshing suspension states...")
        t_start = time()

        # Get suspension states from API
        states_by_account = self.client.refresh_suspension_states(accounts)

        # Save to database with audit trail
        for account_url, server_states in states_by_account.items():
            self.db.save_suspension_states(
                account_url, server_states, create_audit=True
            )

        log.info(
            "Refreshed suspension states for %d accounts in %.2f seconds",
            len(states_by_account),
            time() - t_start,
        )

        self._last_suspension_check = now

    def refresh_accounts(self) -> list[Account]:
        log.info("Refreshing accounts...")
        t_start = time()

        verified_accounts, verified_urls, verified_fetch_failed = (
            self._fetch_verified_accounts()
        )
        all_accounts_by_url = self._merge_with_db_accounts(verified_accounts)
        deleted_urls = self._collect_initial_deleted_urls(all_accounts_by_url)

        if not verified_fetch_failed:
            self._apply_source_removal(
                all_accounts_by_url, verified_urls, deleted_urls
            )

        refreshed_accounts = self._refresh_accounts_concurrently(
            all_accounts_by_url, deleted_urls
        )
        self.db.save_accounts(refreshed_accounts)

        active_accounts = [
            account for account in refreshed_accounts if account.url not in deleted_urls
        ]
        self._refresh_posts_and_media(active_accounts)

        log.info(
            "Refreshed %d accounts in %.2f seconds.",
            len(refreshed_accounts),
            time() - t_start,
        )
        return refreshed_accounts

    def _fetch_verified_accounts(self) -> tuple[list[Account], set[str], bool]:
        verified_accounts: list[Account] = []
        verified_fetch_failed = False
        try:
            verified_accounts = self.client.get_verified_accounts()
        except Exception as exc:
            log.error("Failed to fetch verified accounts: %s", exc)
            verified_fetch_failed = True

        verified_urls = {account.url for account in verified_accounts}
        return verified_accounts, verified_urls, verified_fetch_failed

    def _merge_with_db_accounts(
        self, verified_accounts: list[Account]
    ) -> dict[str, Account]:
        # Start with all DB accounts so deleted/removed accounts are still
        # refreshed and recovery can be detected.
        all_accounts_by_url = self.db.get_accounts()
        for verified in verified_accounts:
            if verified.url not in all_accounts_by_url:
                all_accounts_by_url[verified.url] = verified
        return all_accounts_by_url

    def _collect_initial_deleted_urls(
        self, all_accounts_by_url: dict[str, Account]
    ) -> set[str]:
        # Pre-populate deleted URLs with the current DB state so that previously
        # deleted accounts that are still unreachable are not treated as active.
        deleted_urls: set[str] = set()
        home_states = self.db.get_home_instance_states(
            list(all_accounts_by_url.keys())
        )
        for url, state in home_states.items():
            if state == SuspensionState.DELETED:
                deleted_urls.add(url)
        return deleted_urls

    def _apply_source_removal(
        self,
        all_accounts_by_url: dict[str, Account],
        verified_urls: set[str],
        deleted_urls: set[str],
    ) -> None:
        now = _naive_utc(datetime.now(timezone.utc))
        for account in list(all_accounts_by_url.values()):
            if account.url not in verified_urls:
                if account.source_removed_since is None:
                    account.source_removed_since = now
                    log.info("Account %s no longer in source", account.url)
                else:
                    down_hours = (
                        now - _naive_utc(account.source_removed_since)
                    ).total_seconds() / 3600
                    if down_hours > self.config.deleted_after_down_hours:
                        log.warning(
                            "Account %s has been removed from source for %.1f hours, marking DELETED",
                            account.url,
                            down_hours,
                        )
                        self._mark_deleted(account, deleted_urls)
            else:
                if account.source_removed_since is not None:
                    account.source_removed_since = None
                    log.info("Account %s reappeared in source", account.url)

    def _mark_deleted(
        self,
        account: Account,
        deleted_urls: set[str],
        *,
        clear_instance_down_since: bool = False,
    ) -> None:
        if clear_instance_down_since:
            account.instance_down_since = None
        self.db.save_suspension_states(
            account.url, {account.instance_url: SuspensionState.DELETED}
        )
        deleted_urls.add(account.url)

    def _handle_refresh_success(
        self, account: Account, deleted_urls: set[str]
    ) -> None:
        # Instance is reachable; clear instance-down tracking.
        account.instance_down_since = None
        # Only reactivate accounts that are not currently removed from source.
        if account.source_removed_since is None:
            current_state = self.db.get_account_state_on_instance(
                account.url, account.instance_url
            )
            if (
                current_state == SuspensionState.DELETED
                or account.url in deleted_urls
            ):
                self.db.save_suspension_states(
                    account.url, {account.instance_url: SuspensionState.ACTIVE}
                )
                deleted_urls.discard(account.url)

    def _handle_temporary_failure(
        self, account: Account, deleted_urls: set[str]
    ) -> None:
        if account.instance_down_since is None:
            account.instance_down_since = _naive_utc(datetime.now(timezone.utc))
        down_hours = (
            _naive_utc(datetime.now(timezone.utc)) - _naive_utc(account.instance_down_since)
        ).total_seconds() / 3600
        if down_hours > self.config.deleted_after_down_hours:
            log.warning(
                "Account %s has been unreachable for %.1f hours, marking DELETED",
                account.url,
                down_hours,
            )
            self._mark_deleted(account, deleted_urls)

    def _refresh_accounts_concurrently(
        self,
        all_accounts_by_url: dict[str, Account],
        deleted_urls: set[str],
    ) -> list[Account]:
        refreshed_accounts: list[Account] = []
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_requests
        ) as executor:
            future_to_account = {
                executor.submit(self.client.refresh_account, account): account
                for account in all_accounts_by_url.values()
            }
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    future.result()
                    refreshed_accounts.append(account)
                    self._handle_refresh_success(account, deleted_urls)
                except AccountDeletedError as exc:
                    log.warning(str(exc))
                    refreshed_accounts.append(account)
                    self._mark_deleted(
                        account, deleted_urls, clear_instance_down_since=True
                    )
                except Exception as exc:
                    if isinstance(exc, HttpError):
                        log.warning(
                            "Temporary error refreshing %s: %s", account.url, exc
                        )
                    else:
                        log.warning(
                            "Error refreshing %s: %s",
                            account.url,
                            exc,
                            exc_info=True,
                        )
                    refreshed_accounts.append(account)
                    self._handle_temporary_failure(account, deleted_urls)
        return refreshed_accounts

    def _refresh_posts_and_media(self, active_accounts: list[Account]) -> None:
        posts = self.client.refresh_posts(active_accounts)
        self.db.save_posts(posts)
        self.client.boost_posts(posts)

        if self.config.download_media:
            self.client.download_account_images(active_accounts)
            self.client.download_attachments(posts)

    def refresh_campaigns(self, accounts: list[Account]) -> list[Campaign]:
        # Merge refreshed accounts with DB accounts that have campaign URLs.
        # This ensures campaigns are still scraped for suspended/unretrievable
        # accounts using their cached campaign URLs.
        accounts_by_url = {account.url: account for account in accounts}
        for db_account in self.db.get_accounts().values():
            if db_account.campaign_url and db_account.url not in accounts_by_url:
                accounts_by_url[db_account.url] = db_account

        campaigns = self.client.refresh_campaigns(list(accounts_by_url.values()))
        self.db.save_campaigns(campaigns)
        return campaigns

    def run(self):
        """
        Run the main loop.
        """
        super().run()
        self._main()

    def stop(self):
        """
        Stop the main loop.
        """
        self.client.stop_campaigns_bot()
        self._stop_event.set()
