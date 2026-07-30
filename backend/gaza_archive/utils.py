from datetime import datetime, timezone


def naive_utc(dt: datetime) -> datetime:
    """Return a naive UTC datetime, converting/removing tzinfo if present."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


__all__ = ["naive_utc"]
