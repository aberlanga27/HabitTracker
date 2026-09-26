"""Time source and the single local-date conversion helper."""

from datetime import UTC, date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current instant as an aware UTC datetime."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)


_system_clock = SystemClock()


def get_clock() -> Clock:
    return _system_clock


def local_date(now_utc: datetime, user_tz: str) -> date:
    """Return the calendar date of `now_utc` in the IANA timezone `user_tz`.

    Raises ValueError for naive datetimes.
    """
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    return now_utc.astimezone(ZoneInfo(user_tz)).date()
