"""Spec 005 day summary API tests: GET /api/v1/days/{date} (FR-004; research R3, R5, R6)."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from tests.factories import check_in, create_habit, register
from tests.fakes import FrozenClock

HABITS = "/api/v1/habits"
DAYS = "/api/v1/days"
TODAY = "2026-09-26"
MONDAY_NOON = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
NEXT_SUNDAY_NOON = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
LATER_FRIDAY_NOON = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
MWF_IN: dict[str, object] = {"type": "weekdays", "weekdays": ["mon", "wed", "fri"]}
THREE_A_WEEK: dict[str, object] = {"type": "times_per_week", "times_per_week": 3}
WEEK = [f"2026-09-{day}" for day in range(21, 28)]
WEEK_IDS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@pytest.fixture
def ana_id(client: TestClient) -> str:
    """Signs `client` in as Ana (UTC) on the default Saturday 2026-09-26."""
    return register(client, email="ana@example.com")["id"]


@pytest.fixture
def monday_ana(client: TestClient, clock: FrozenClock) -> str:
    """Signs `client` in as Ana (UTC) with the clock on Monday 2026-09-21 12:00Z."""
    clock.set(MONDAY_NOON)
    return register(client, email="ana@example.com")["id"]


@pytest.fixture
def other(app: FastAPI) -> Iterator[TestClient]:
    """A second signed-in client for Ben."""
    with TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"}) as other_client:
        register(other_client, email="ben@example.com")
        yield other_client


def _get_day(client: TestClient, day: str) -> Response:
    resp: Response = client.get(f"{DAYS}/{day}")
    return resp


def _day(client: TestClient, day: str) -> dict[str, Any]:
    resp = _get_day(client, day)
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _ids(client: TestClient, day: str) -> list[str]:
    return [item["habit"]["id"] for item in _day(client, day)["items"]]


def _item(client: TestClient, day: str, habit_id: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = _day(client, day)["items"]
    matches = [item for item in items if item["habit"]["id"] == habit_id]
    assert len(matches) == 1, f"habit {habit_id} listed {len(matches)} times on {day}: {items}"
    return matches[0]


def _state(client: TestClient, day: str, habit_id: str) -> tuple[str, bool, Any]:
    item = _item(client, day, habit_id)
    return item["status"], item["completed"], item["week"]


def _week(completed: int, target: int) -> dict[str, int]:
    return {"completed": completed, "target": target}


def _three_a_week_with_check_ins(
    client: TestClient, clock: FrozenClock, days: tuple[str, ...], **schedule: object
) -> str:
    """Creates a habit on Monday 2026-09-21, then checks in on `days` from Friday 2026-10-02."""
    habit_id: str = create_habit(client, schedule=schedule or THREE_A_WEEK)["id"]
    clock.set(LATER_FRIDAY_NOON)
    for day in days:
        check_in(client, habit_id, day)
    return habit_id


def _assert_validation_error(resp: Response) -> None:
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# --- Authentication and input -------------------------------------------------


def test_days_requires_authentication(client: TestClient) -> None:
    resp = _get_day(client, TODAY)
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", ["2026-13-01", "2026-02-30", "today", "20260926"])
def test_fr004_malformed_date_is_validation_error(client: TestClient, day: str) -> None:
    _assert_validation_error(_get_day(client, day))


# --- US1 Daily default (FR-004) -----------------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_fr004_day_summary_lists_due_habit_with_completion(client: TestClient) -> None:
    habit = create_habit(client)
    assert _day(client, TODAY) == {
        "date": TODAY,
        "items": [
            {"habit": habit, "status": "due", "completed": False, "note": None, "week": None}
        ],
    }


@pytest.mark.usefixtures("ana_id")
def test_fr004_day_summary_for_user_without_habits_is_empty(client: TestClient) -> None:
    assert _day(client, TODAY) == {"date": TODAY, "items": []}


@pytest.mark.usefixtures("monday_ana")
@pytest.mark.parametrize("day", WEEK, ids=WEEK_IDS)
def test_us1_s1_fr004_daily_habit_is_due_every_day_of_a_week(
    client: TestClient, clock: FrozenClock, day: str
) -> None:
    habit_id = create_habit(client)["id"]
    clock.set(NEXT_SUNDAY_NOON)
    assert _state(client, day, habit_id) == ("due", False, None)


@pytest.mark.usefixtures("ana_id")
def test_r3_daily_habit_created_today_is_listed_for_yesterday(client: TestClient) -> None:
    habit_id = create_habit(client)["id"]
    assert _state(client, "2026-09-25", habit_id) == ("due", False, None)


@pytest.mark.usefixtures("ana_id")
def test_r3_dates_before_first_schedule_use_first_schedule(client: TestClient) -> None:
    habit_id = create_habit(client, schedule=MWF_IN)["id"]
    assert habit_id in _ids(client, "2026-09-25")
    assert habit_id not in _ids(client, "2026-09-24")


@pytest.mark.usefixtures("ana_id")
def test_fr004_completed_and_note_reflect_check_in_on_that_date(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="felt great")
    assert _item(client, TODAY, habit["id"]) == {
        "habit": habit,
        "status": "due",
        "completed": True,
        "note": "felt great",
        "week": None,
    }


@pytest.mark.usefixtures("ana_id")
def test_fr004_check_in_on_another_date_does_not_mark_completed(client: TestClient) -> None:
    habit_id = create_habit(client)["id"]
    check_in(client, habit_id, "2026-09-25", note="yesterday")
    item = _item(client, TODAY, habit_id)
    assert (item["completed"], item["note"]) == (False, None)


@pytest.mark.usefixtures("ana_id")
def test_fr004_undone_check_in_is_not_completed(client: TestClient) -> None:
    habit_id = create_habit(client)["id"]
    check_in(client, habit_id, TODAY)
    check_in(client, habit_id, TODAY, completed=False)
    assert _item(client, TODAY, habit_id)["completed"] is False


@pytest.mark.usefixtures("ana_id")
def test_r6_items_are_ordered_by_position(client: TestClient) -> None:
    first = create_habit(client, name="Read")["id"]
    second = create_habit(client, name="Walk")["id"]
    third = create_habit(client, name="Stretch")["id"]
    resp = client.put(f"{HABITS}/order", json={"habit_ids": [third, first, second]})
    assert resp.status_code == 200, resp.text
    assert _ids(client, TODAY) == [third, first, second]


@pytest.mark.usefixtures("ana_id")
def test_r6_archived_habits_are_omitted(client: TestClient) -> None:
    kept = create_habit(client, name="Read")["id"]
    archived = create_habit(client, name="Walk")["id"]
    assert client.post(f"{HABITS}/{archived}/archive").status_code == 200
    assert _ids(client, TODAY) == [kept]


@pytest.mark.usefixtures("ana_id")
def test_r6_other_users_habits_are_never_listed(client: TestClient, other: TestClient) -> None:
    ana_habit = create_habit(client, name="Ana's habit")["id"]
    ben_habit = create_habit(other, name="Ben's habit")["id"]
    check_in(other, ben_habit, TODAY)
    assert _ids(client, TODAY) == [ana_habit]
    assert _ids(other, TODAY) == [ben_habit]


@pytest.mark.usefixtures("ana_id")
def test_r6_week_is_null_for_daily_and_weekdays_habits(client: TestClient) -> None:
    create_habit(client, name="Daily")
    create_habit(client, name="Weekend", schedule={"type": "weekdays", "weekdays": ["sat"]})
    assert [item["week"] for item in _day(client, TODAY)["items"]] == [None, None]


# --- US2 Specific weekdays (FR-004) -------------------------------------------


@pytest.mark.usefixtures("monday_ana")
@pytest.mark.parametrize(
    ("day", "listed"),
    list(zip(WEEK, [True, False, True, False, True, False, False], strict=True)),
    ids=WEEK_IDS,
)
def test_us2_s1_fr004_mwf_habit_listed_only_on_mon_wed_fri(
    client: TestClient, clock: FrozenClock, day: str, listed: bool
) -> None:
    habit_id = create_habit(client, schedule=MWF_IN)["id"]
    clock.set(NEXT_SUNDAY_NOON)
    assert (habit_id in _ids(client, day)) is listed


@pytest.mark.usefixtures("monday_ana")
def test_us2_s1_fr004_mwf_habit_not_due_on_tuesday(client: TestClient, clock: FrozenClock) -> None:
    daily = create_habit(client, name="Read")["id"]
    gym = create_habit(client, name="Gym", schedule=MWF_IN)["id"]
    clock.set(NEXT_SUNDAY_NOON)
    assert _ids(client, "2026-09-22") == [daily]
    assert _ids(client, "2026-09-23") == [daily, gym]


@pytest.mark.usefixtures("monday_ana")
def test_us2_s1_fr004_listed_mwf_habit_is_due(client: TestClient, clock: FrozenClock) -> None:
    habit_id = create_habit(client, schedule=MWF_IN)["id"]
    clock.set(NEXT_SUNDAY_NOON)
    assert _state(client, "2026-09-23", habit_id) == ("due", False, None)


def test_us2_fr004_weekday_follows_users_local_date(client: TestClient, clock: FrozenClock) -> None:
    # 04:30Z Tuesday is 23:30 Monday in Mexico City.
    clock.set(datetime(2026, 9, 29, 4, 30, tzinfo=UTC))
    register(client, email="ana@example.com", timezone="America/Mexico_City")
    habit = create_habit(client, schedule=MWF_IN)
    assert habit["schedule"]["effective_from"] == "2026-09-28"
    check_in(client, habit["id"], "2026-09-28")
    assert _state(client, "2026-09-28", habit["id"]) == ("due", True, None)
    assert habit["id"] not in _ids(client, "2026-09-27")


@dataclass(frozen=True)
class DstDay:
    now: datetime
    local_date: str


DST_DAYS = [
    DstDay(datetime(2026, 3, 29, 21, 59, tzinfo=UTC), "2026-03-29"),
    DstDay(datetime(2026, 10, 25, 22, 59, tzinfo=UTC), "2026-10-25"),
]


@pytest.mark.parametrize("case", DST_DAYS, ids=["spring-forward-sunday", "fall-back-sunday"])
def test_fr004_sunday_habit_due_on_dst_day_with_2359_local_check_in(
    client: TestClient, clock: FrozenClock, case: DstDay
) -> None:
    clock.set(case.now)
    register(client, email="ana@example.com", timezone="Europe/Madrid")
    habit = create_habit(client, schedule={"type": "weekdays", "weekdays": ["sun"]})
    check_in(client, habit["id"], case.local_date)
    assert _state(client, case.local_date, habit["id"]) == ("due", True, None)


# --- US3 N times per week (FR-003, FR-004; research R5) -----------------------


@pytest.mark.usefixtures("monday_ana")
def test_us3_s1_fr004_two_check_ins_this_week_is_due_with_2_of_3(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _three_a_week_with_check_ins(client, clock, ("2026-09-21", "2026-09-22"))
    assert _state(client, "2026-09-24", habit_id) == ("due", False, _week(2, 3))


@pytest.mark.usefixtures("monday_ana")
def test_us3_s2_fr004_three_check_ins_before_date_is_done_for_week(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert _state(client, "2026-09-24", habit_id) == ("done_for_week", False, _week(3, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_day_of_third_check_in_stays_due_and_completed(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert _state(client, "2026-09-23", habit_id) == ("due", True, _week(3, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_week_counts_check_ins_through_the_date(client: TestClient, clock: FrozenClock) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert _state(client, "2026-09-21", habit_id) == ("due", True, _week(1, 3))
    assert _state(client, "2026-09-22", habit_id) == ("due", True, _week(2, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_sunday_is_still_done_for_week(client: TestClient, clock: FrozenClock) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert _state(client, "2026-09-27", habit_id) == ("done_for_week", False, _week(3, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_week_resets_on_monday(client: TestClient, clock: FrozenClock) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert _state(client, "2026-09-28", habit_id) == ("due", False, _week(0, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_week_spanning_month_boundary_counts_both_months(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _three_a_week_with_check_ins(
        client, clock, ("2026-09-28", "2026-09-30"), type="times_per_week", times_per_week=2
    )
    assert _state(client, "2026-10-01", habit_id) == ("done_for_week", False, _week(2, 2))


@pytest.mark.usefixtures("monday_ana")
def test_r5_week_counts_only_this_habits_check_ins(client: TestClient, clock: FrozenClock) -> None:
    busy = create_habit(client, name="Busy", schedule=THREE_A_WEEK)["id"]
    idle = create_habit(client, name="Idle", schedule=THREE_A_WEEK)["id"]
    clock.set(LATER_FRIDAY_NOON)
    for day in ("2026-09-21", "2026-09-22", "2026-09-23"):
        check_in(client, busy, day)
    assert _state(client, "2026-09-24", busy) == ("done_for_week", False, _week(3, 3))
    assert _state(client, "2026-09-24", idle) == ("due", False, _week(0, 3))


@pytest.mark.usefixtures("monday_ana")
def test_r5_undone_check_in_does_not_count_toward_week(
    client: TestClient, clock: FrozenClock
) -> None:
    habit_id = _three_a_week_with_check_ins(client, clock, ("2026-09-21",))
    check_in(client, habit_id, "2026-09-21", completed=False)
    assert _state(client, "2026-09-22", habit_id) == ("due", False, _week(0, 3))


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", ["2026-09-20", "2026-09-25", TODAY], ids=["sun", "fri", "sat"])
def test_edge_fr003_seven_times_per_week_is_listed_as_daily(client: TestClient, day: str) -> None:
    habit = create_habit(client, schedule={"type": "times_per_week", "times_per_week": 7})
    item = _item(client, day, habit["id"])
    assert (item["status"], item["week"]) == ("due", None)
    assert item["habit"]["schedule"]["type"] == "daily"


@pytest.mark.usefixtures("monday_ana")
def test_r5_daily_habit_is_never_done_for_week(client: TestClient, clock: FrozenClock) -> None:
    habit_id = create_habit(client)["id"]
    clock.set(LATER_FRIDAY_NOON)
    for day in WEEK[:6]:
        check_in(client, habit_id, day)
    assert _state(client, "2026-09-27", habit_id) == ("due", False, None)
