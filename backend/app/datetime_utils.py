from datetime import datetime, timezone


UTC = timezone.utc


def ensure_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime; naive provider values are documented UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_utc_datetime(value: str | None, *, default: datetime | None = None) -> datetime:
    """Parse an ISO-8601 provider timestamp whose offset-less form means UTC."""
    if not value:
        return ensure_utc(default) if default is not None else datetime.now(UTC)
    return ensure_utc(datetime.fromisoformat(value.strip().replace("Z", "+00:00")))
