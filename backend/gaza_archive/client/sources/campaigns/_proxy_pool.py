import logging
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

log = logging.getLogger(__name__)


class ProxyPool:
    """
    Thread-safe pool of HTTP(S) or SOCKS proxies with round-robin selection
    and per-proxy cool-down periods.

    Proxies that are rate-limited or fail are put in cool-down for a
    configurable amount of time, during which they are skipped by `acquire()`.
    """

    #: Upper bound for a single cool-down period, so a very large Retry-After
    #: can't park a proxy forever.
    _max_cooldown = 300.0

    def __init__(self, proxies: list[str] | None, cooldown: float = 60.0):
        # Accept proxies given as host:port without a scheme.
        self._proxies = [
            proxy if "://" in proxy else f"http://{proxy}" for proxy in (proxies or [])
        ]
        self._cooldown = cooldown
        #: proxy URL -> monotonic timestamp when its cool-down ends
        self._cooled_until: dict[str, float] = {}
        self._index = 0
        self._lock = Lock()

    def __len__(self) -> int:
        """
        :return: Number of proxies in the pool.
        """
        return len(self._proxies)

    def __bool__(self) -> bool:
        """
        :return: True if the pool is not empty.
        """
        return bool(self._proxies)

    def acquire(self) -> str | None:
        """
        Return the next proxy in round-robin order that is not in cool-down,
        or None if every proxy is currently cooling down.
        """
        with self._lock:
            now = monotonic()
            size = len(self._proxies)
            for offset in range(size):
                proxy = self._proxies[(self._index + offset) % size]
                if self._cooled_until.get(proxy, 0.0) <= now:
                    self._index = (self._index + offset + 1) % size
                    return proxy
            return None

    def cooldown_remaining(self) -> float:
        """
        Seconds until the soonest proxy leaves cool-down, or 0 if a proxy is
        available right now.
        """
        with self._lock:
            now = monotonic()
            remaining = [
                self._cooled_until.get(proxy, 0.0) - now for proxy in self._proxies
            ]
            return max(min(remaining), 0.0) if remaining else 0.0

    def report_rate_limited(self, proxy: str, retry_after: float | None = None):
        """
        Mark a proxy as rate-limited. It stays in cool-down for `retry_after`
        seconds (from the upstream Retry-After header) if provided, otherwise
        for the configured cool-down period.
        """
        duration = (
            retry_after
            if retry_after is not None and retry_after > 0
            else self._cooldown
        )
        self._cool(proxy, duration, "rate-limited")

    def report_failure(self, proxy: str):
        """
        Mark a proxy as failing (e.g. connection errors). It stays in
        cool-down for the configured cool-down period.
        """
        self._cool(proxy, self._cooldown, "failure")

    def _cool(self, proxy: str, duration: float, reason: str):
        duration = max(1.0, min(duration, self._max_cooldown))
        with self._lock:
            self._cooled_until[proxy] = monotonic() + duration
        # Log only the host: proxy URLs may embed credentials.
        log.debug(
            "Cooling down proxy %s for %.0f seconds (%s)",
            urlsplit(proxy).hostname or proxy,
            duration,
            reason,
        )
