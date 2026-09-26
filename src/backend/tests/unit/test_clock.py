from datetime import UTC, date, datetime, timedelta

from app.core.clock import local_date
from tests.fakes import FrozenClock


def test_local_date_2359_local_counts_for_local_date_not_utc() -> None:
    # 23:59 in Mexico City (UTC-6) is 05:59 UTC the next day.
    now_utc = datetime(2026, 9, 27, 5, 59, tzinfo=UTC)
    assert local_date(now_utc, "America/Mexico_City") == date(2026, 9, 26)


def test_local_date_east_of_utc_rolls_forward() -> None:
    now_utc = datetime(2026, 9, 26, 22, 30, tzinfo=UTC)
    assert local_date(now_utc, "Asia/Tokyo") == date(2026, 9, 27)


def test_local_date_dst_spring_forward_does_not_skip_a_day() -> None:
    # Europe/Madrid springs forward on 2026-03-29 at 02:00 local.
    before = datetime(2026, 3, 28, 23, 30, tzinfo=UTC)  # 00:30 local on the 29th
    after = datetime(2026, 3, 29, 21, 59, tzinfo=UTC)  # 23:59 local on the 29th
    assert local_date(before, "Europe/Madrid") == date(2026, 3, 29)
    assert local_date(after, "Europe/Madrid") == date(2026, 3, 29)


def test_local_date_rejects_naive_datetime() -> None:
    try:
        local_date(datetime(2026, 9, 26, 12, 0), "UTC")  # noqa: DTZ001
    except ValueError:
        return
    raise AssertionError("naive datetime must be rejected")


def test_frozen_clock_advances() -> None:
    clock = FrozenClock(datetime(2026, 9, 26, 12, 0, tzinfo=UTC))
    clock.advance(timedelta(days=1))
    assert clock.now() == datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
