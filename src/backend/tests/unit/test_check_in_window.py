"""Spec 003 editable date window (FR-002, FR-003; research R3): today-30 .. today inclusive."""

from datetime import date

import pytest
from app.services.check_ins import editable_window, is_editable

TODAY = date(2026, 9, 26)


def test_fr002_window_is_today_minus_30_through_today() -> None:
    assert editable_window(TODAY) == (date(2026, 8, 27), date(2026, 9, 26))


@pytest.mark.parametrize(
    ("today", "earliest"),
    [
        (date(2026, 3, 1), date(2026, 1, 30)),
        (date(2028, 3, 1), date(2028, 1, 31)),
        (date(2027, 1, 15), date(2026, 12, 16)),
        (date(2026, 10, 25), date(2026, 9, 25)),
    ],
    ids=["across-february", "across-leap-february", "across-new-year", "dst-fall-back-day"],
)
def test_fr002_window_crosses_month_and_year_boundaries(today: date, earliest: date) -> None:
    assert editable_window(today) == (earliest, today)


@pytest.mark.parametrize(
    "day",
    [date(2026, 9, 26), date(2026, 9, 25), date(2026, 8, 27)],
    ids=["today", "yesterday", "today-30"],
)
def test_fr002_days_inside_window_are_editable(day: date) -> None:
    assert is_editable(day, TODAY) is True


@pytest.mark.parametrize(
    "day",
    [date(2026, 9, 27), date(2026, 8, 26), date(2027, 9, 26), date(2025, 9, 26)],
    ids=["tomorrow", "today-31", "next-year", "last-year"],
)
def test_fr003_future_or_older_than_30_days_is_not_editable(day: date) -> None:
    assert is_editable(day, TODAY) is False


@pytest.mark.parametrize(
    ("day", "today", "expected"),
    [
        (date(2026, 12, 31), date(2027, 1, 1), True),
        (date(2026, 12, 1), date(2026, 12, 31), True),
        (date(2026, 11, 30), date(2026, 12, 31), False),
        (date(2027, 1, 1), date(2026, 12, 31), False),
        (date(2028, 1, 31), date(2028, 3, 1), True),
        (date(2028, 1, 30), date(2028, 3, 1), False),
    ],
    ids=[
        "yesterday-across-new-year",
        "today-30-same-month",
        "today-31-across-month",
        "tomorrow-across-new-year",
        "today-30-leap-year",
        "today-31-leap-year",
    ],
)
def test_fr003_is_editable_at_month_and_year_boundaries(
    day: date, today: date, expected: bool
) -> None:
    assert is_editable(day, today) is expected
