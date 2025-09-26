from abc import ABC


class Error(Exception, ABC):
    """
    Base class for all custom errors.
    """

    def __init__(self, message: str, exception: Exception | None = None, *args, **_):
        self.message = message
        self.exception = exception
        super().__init__(message, *args)


class HttpError(Error, RuntimeError):
    """
    Represents an HTTP error with a status code, message, and optional exception.
    """

    def __init__(self, *args, status_code: int = 500, **kwargs):
        self.status_code = status_code
        super().__init__(*args, **kwargs)


class AccountError(Error):
    """
    General account-related error.
    """

    def __init__(self, *args, account: str = "", **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)


class AccountNotFoundError(AccountError, LookupError):
    """
    Raised when an account is not found.
    """


class DownloadError(Error, RuntimeError):
    """
    Raised when a download operation fails.
    """
