from datetime import datetime
from zoneinfo import ZoneInfo


def to_restaurant_time(dt: datetime, tz: str) -> datetime:
    """Convert a naive or UTC datetime to the restaurant's local timezone."""
    zone = ZoneInfo(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(zone)
    return dt.astimezone(zone)


def now_in_restaurant_time(tz: str) -> datetime:
    """Return the current time in the restaurant's local timezone."""
    return datetime.now(ZoneInfo(tz))
