"""Test doubles shared across the suite."""

from datetime import datetime, timedelta


class FrozenClock:
    """A controllable clock; `now()` returns the set instant until moved."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("instant must be timezone-aware")
        self._instant = instant

    def now(self) -> datetime:
        return self._instant

    def set(self, instant: datetime) -> None:
        self._instant = instant

    def advance(self, delta: timedelta) -> None:
        self._instant += delta
