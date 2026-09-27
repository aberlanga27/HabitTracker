"""Spec 004 streak exposure API tests (FR-001..FR-005; research R2, R3)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from tests.factories import check_in, create_habit, register
from tests.fakes import FrozenClock

HABITS = "/api/v1/habits"
DAYS = "/api/v1/days"
TODAY = "2026-09-26"  # Saturday; default clock is 2026-09-26T12:00Z
MONDAY_NOON = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
THURSDAY_NOON = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
SATURDAY_NOON = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
DAYS_LATER = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
TOKYO_EVENING_UTC = datetime(2026, 9, 26, 22, 30, tzinfo=UTC)  # 2026-09-27 07:30 in Tokyo
MWF_IN: dict[str, object] = {"type": "weekdays", "weekdays": ["mon", "wed", "fri"]}
ZERO: dict[str, object] = {
    "current": 0,
    "current_start": None,
    "longest": 0,
    "longest_start": None,
    "longest_end": None,
}
THREE_DAYS: dict[str, object] = {
    "current": 3,
    "current_start": "2026-09-24",
    "longest": 3,
    "longest_start": "2026-09-24",
    "longest_end": "2026-09-26",
}


def _streak_of(
    current: int, current_start: str | None, longest: int, longest_range: tuple[str, str] | None
) -> dict[str, object]:
    start, end = longest_range or (None, None)
    return {
        "current": current,
        "current_start": current_start,
        "longest": longest,
        "longest_start": start,
        "longest_end": end,
    }


@pytest.fixture
def ana_id(client: TestClient) -> str:
    """Signs `client` in as Ana (UTC) on the default Saturday 2026-09-26."""
    return register(client, email="ana@example.com")["id"]


def _ok(resp: Response) -> dict[str, Any]:
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _only(habits: list[dict[str, Any]], habit_id: str) -> dict[str, Any]:
    matches = [habit for habit in habits if habit["id"] == habit_id]
    assert len(matches) == 1, f"habit {habit_id} listed {len(matches)} times: {habits}"
    return matches[0]


def _habit(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.get(f"{HABITS}/{habit_id}"))


def _streak(client: TestClient, habit_id: str) -> dict[str, Any]:
    streak: dict[str, Any] = _habit(client, habit_id)["streak"]
    return streak


def _habit_with_check_ins(client: TestClient, *days: str, **fields: object) -> str:
    habit_id: str = create_habit(client, **fields)["id"]
    for day in days:
        check_in(client, habit_id, day)
    return habit_id


def _day_habit(client: TestClient, day: str, habit_id: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = _ok(client.get(f"{DAYS}/{day}"))["items"]
    return _only([item["habit"] for item in items], habit_id)


# --- FR-005 exposure on every HabitRead ---------------------------------------


def _via_list(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _only(_ok(client.get(HABITS))["items"], habit_id)


def _via_patch(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.patch(f"{HABITS}/{habit_id}", json={"name": "Walk"}))


def _via_archive(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.post(f"{HABITS}/{habit_id}/archive"))


def _via_restore(client: TestClient, habit_id: str) -> dict[str, Any]:
    _via_archive(client, habit_id)
    return _ok(client.post(f"{HABITS}/{habit_id}/restore"))


def _via_order(client: TestClient, habit_id: str) -> dict[str, Any]:
    body = _ok(client.put(f"{HABITS}/order", json={"habit_ids": [habit_id]}))
    return _only(body["items"], habit_id)


def _via_day(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _day_habit(client, TODAY, habit_id)


EXPOSURES: dict[str, Callable[[TestClient, str], dict[str, Any]]] = {
    "list": _via_list,
    "detail": _habit,
    "patch": _via_patch,
    "archive": _via_archive,
    "restore": _via_restore,
    "order": _via_order,
    "day-summary": _via_day,
}


@pytest.mark.usefixtures("ana_id")
def test_fr005_created_habit_response_has_zero_streak(client: TestClient) -> None:
    assert create_habit(client)["streak"] == ZERO


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("exposure", list(EXPOSURES))
def test_fr005_new_habit_has_zero_streak_in_every_response(
    client: TestClient, exposure: str
) -> None:
    habit_id = create_habit(client)["id"]
    assert EXPOSURES[exposure](client, habit_id)["streak"] == ZERO


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("exposure", list(EXPOSURES))
def test_fr005_every_habit_response_carries_current_streak(
    client: TestClient, exposure: str
) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25", TODAY)
    assert EXPOSURES[exposure](client, habit_id)["streak"] == THREE_DAYS


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", [TODAY, "2026-09-25"], ids=["today", "yesterday"])
def test_fr005_day_summary_habit_streak_equals_habit_detail(client: TestClient, day: str) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25", TODAY)
    item_habit = _day_habit(client, day, habit_id)
    assert item_habit["streak"] == _streak(client, habit_id)
    assert item_habit == _habit(client, habit_id)


# --- US1 Current streak (FR-001, FR-004) --------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_three_consecutive_days_including_today_is_3(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25", TODAY)
    assert _streak(client, habit_id) == THREE_DAYS


@pytest.mark.usefixtures("ana_id")
def test_us1_s2_fr001_yesterday_still_counts_before_today_ends(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25")
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-24", 2, ("2026-09-24", "2026-09-25"))


@pytest.mark.usefixtures("ana_id")
def test_us1_s3_fr001_gap_two_days_ago_counts_only_days_after_gap(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(
        client, "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-25", TODAY
    )
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-25", 3, ("2026-09-21", "2026-09-23"))


@pytest.mark.usefixtures("ana_id")
def test_edge_fr001_habit_created_today_with_one_check_in_is_1(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(client, TODAY)
    assert _streak(client, habit_id) == _streak_of(1, TODAY, 1, (TODAY, TODAY))


@pytest.mark.usefixtures("ana_id")
def test_fr004_check_in_today_updates_streak_in_next_response(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25")
    assert _streak(client, habit_id)["current"] == 2
    check_in(client, habit_id, TODAY)
    assert _streak(client, habit_id) == THREE_DAYS


@pytest.mark.usefixtures("ana_id")
def test_edge_fr004_undo_today_recalculates_streak_immediately(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25", TODAY)
    check_in(client, habit_id, TODAY, completed=False)
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-24", 2, ("2026-09-24", "2026-09-25"))


# --- User timezone for "today" (edge case) ------------------------------------


def test_edge_fr001_today_is_the_users_local_date(client: TestClient, clock: FrozenClock) -> None:
    clock.set(TOKYO_EVENING_UTC)
    register(client, email="ana@example.com", timezone="Asia/Tokyo")
    habit_id = _habit_with_check_ins(client, "2026-09-26", "2026-09-27")
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-26", 2, ("2026-09-26", "2026-09-27"))


def test_edge_fr001_at_2359_local_today_is_still_pending(
    client: TestClient, clock: FrozenClock
) -> None:
    # 05:59Z on 27 Sep is 23:59 on 26 Sep in Mexico City (UTC-6).
    clock.set(datetime(2026, 9, 27, 5, 59, tzinfo=UTC))
    register(client, email="ana@example.com", timezone="America/Mexico_City")
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25")
    assert _streak(client, habit_id)["current"] == 2
    check_in(client, habit_id, "2026-09-26")
    assert _streak(client, habit_id) == THREE_DAYS


@dataclass(frozen=True)
class DstDay:
    now: datetime
    local_date: date


DST_DAYS = [
    DstDay(datetime(2026, 3, 29, 21, 59, tzinfo=UTC), date(2026, 3, 29)),
    DstDay(datetime(2026, 10, 25, 22, 59, tzinfo=UTC), date(2026, 10, 25)),
]


@pytest.mark.parametrize("case", DST_DAYS, ids=["spring-forward-sunday", "fall-back-sunday"])
def test_edge_fr001_streak_across_dst_day_with_2359_local_check_in(
    client: TestClient, clock: FrozenClock, case: DstDay
) -> None:
    clock.set(case.now)
    register(client, email="ana@example.com", timezone="Europe/Madrid")
    days = [(case.local_date - timedelta(days=back)).isoformat() for back in (2, 1, 0)]
    habit_id = _habit_with_check_ins(client, *days)
    expected = _streak_of(3, days[0], 3, (days[0], days[-1]))
    assert _streak(client, habit_id) == expected
    clock.advance(timedelta(minutes=1))  # 00:00 local the next day: pending, not broken
    assert _streak(client, habit_id) == expected


# --- US2 Longest streak (FR-002) ----------------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us2_s1_fr002_longest_streak_with_its_date_range(client: TestClient) -> None:
    habit_id = _habit_with_check_ins(
        client, *[f"2026-09-{day}" for day in (15, 16, 17, 18, 19, 25, 26)]
    )
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-25", 5, ("2026-09-15", "2026-09-19"))


# --- US3 Streaks respect schedules (FR-003) -----------------------------------


@pytest.fixture
def mwf_habit_id(client: TestClient, clock: FrozenClock) -> str:
    """Ana's Mon/Wed/Fri habit created Monday 2026-09-21, checked in Mon 21 and Wed 23."""
    clock.set(MONDAY_NOON)
    register(client, email="ana@example.com")
    habit_id: str = create_habit(client, schedule=MWF_IN)["id"]
    clock.set(THURSDAY_NOON)
    check_in(client, habit_id, "2026-09-21")
    check_in(client, habit_id, "2026-09-23")
    return habit_id


def test_us3_s1_fr003_mwf_completed_mon_and_wed_is_2_on_thursday(
    client: TestClient, mwf_habit_id: str
) -> None:
    assert _streak(client, mwf_habit_id) == _streak_of(
        2, "2026-09-21", 2, ("2026-09-21", "2026-09-23")
    )


def test_us3_s2_fr003_mwf_not_completed_friday_is_0_on_saturday(
    client: TestClient, clock: FrozenClock, mwf_habit_id: str
) -> None:
    clock.set(SATURDAY_NOON)
    assert _streak(client, mwf_habit_id) == _streak_of(0, None, 2, ("2026-09-21", "2026-09-23"))


# --- Archived habits freeze (edge case; research R2) --------------------------


@pytest.mark.usefixtures("ana_id")
def test_edge_r2_archived_habit_keeps_frozen_streak_after_days_pass(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _habit_with_check_ins(client, "2026-09-24", "2026-09-25", TODAY)
    _via_archive(client, habit_id)
    clock.set(DAYS_LATER)
    assert _streak(client, habit_id) == THREE_DAYS
    archived = _ok(client.get(HABITS, params={"archived": "true"}))["items"]
    assert _only(archived, habit_id)["streak"] == THREE_DAYS


def test_edge_r2_archived_streak_freezes_at_local_archive_date(
    client: TestClient, clock: FrozenClock
) -> None:
    clock.set(TOKYO_EVENING_UTC)
    register(client, email="ana@example.com", timezone="Asia/Tokyo")
    habit_id = _habit_with_check_ins(client, "2026-09-26", "2026-09-27")
    _via_archive(client, habit_id)
    clock.set(DAYS_LATER)
    assert _streak(client, habit_id) == _streak_of(2, "2026-09-26", 2, ("2026-09-26", "2026-09-27"))
