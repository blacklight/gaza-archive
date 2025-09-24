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
