import requests
from bs4 import BeautifulSoup

from ..config import Config
from ..errors import HttpError
from ..model import Account


class AccountsParser:
    """
    Parser for verified accounts from a given source URL

    :param accounts_source_url: URL to fetch verified accounts from
        (default: `https://gaza-verified.org` or value of `ACCOUNTS_SOURCE_URL`
        env var)
    """

    def __init__(self, config: Config):
        self.config = config

    def _extract_accounts(self, html: str) -> list[Account]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            Account(url=str(elem["href"]))
            for elem in soup.find_all(attrs={"rel": "me"})
            if elem.get("href")
            # Exclude the author of the campaign
            and not str(elem.get("href", "")).endswith("/@aral")
        ]

    def parse(self) -> list[str]:
        try:
            response = requests.get(
                self.config.accounts_source_url, timeout=self.config.http_timeout
            )
            response.raise_for_status()
            return self._extract_accounts(response.text)
        except requests.RequestException as exc:
            raise HttpError(
                f"Failed to fetch accounts from {self.config.accounts_source_url}"
            ) from exc
