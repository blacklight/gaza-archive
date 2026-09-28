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

    #: Status codes that indicate throttling or access denial. These mean
    #: that the resource state couldn't be determined - they are not
    #: evidence that the resource is gone.
    THROTTLED_STATUS_CODES = frozenset({401, 403, 429})

    def __init__(self, *args, status_code: int = 500, **kwargs):
        self.status_code = status_code
        super().__init__(*args, **kwargs)

    @property
    def is_throttled(self) -> bool:
        return self.status_code in self.THROTTLED_STATUS_CODES


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


class AccountDeletedError(AccountNotFoundError):
    """
    Raised when an account is permanently deleted (HTTP 404/410 or other 4xx).
    """


class CampaignDeletedError(Error):
    """
    Raised when a campaign is permanently deleted at the source.
    """

    def __init__(
        self,
        *args,
        campaign_url: str = "",
        status_code: int = 404,
        **kwargs,
    ):
        self.campaign_url = campaign_url
        self.status_code = status_code
        super().__init__(*args, **kwargs)


class DownloadError(Error, RuntimeError):
    """
    Raised when a download operation fails.
    """
