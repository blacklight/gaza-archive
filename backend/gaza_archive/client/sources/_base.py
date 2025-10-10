from abc import ABC, abstractmethod

from ...model import Account


class AccountsSource(ABC):  # pylint: disable=too-few-public-methods
    """
    Base class for different account sources.
    """

    @abstractmethod
    def get_verified_accounts(self) -> list[Account]: ...
