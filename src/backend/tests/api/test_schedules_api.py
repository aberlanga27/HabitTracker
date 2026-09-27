"""Spec 005 Habit Schedules API tests: schedule on habit create/read/update (FR-001..FR-006)."""

from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session, select

from app.core.db import build_engine
from app.models import CheckIn, Habit, Schedule
from tests.factories import check_in, create_habit, make_user, register
from tests.fakes import FrozenClock

BACKEND_ROOT = Path(__file__).resolve().parents[2]
HABITS = "/api/v1/habits"
DAYS = "/api/v1/days"
TODAY = "2026-09-26"
MONDAY_NOON = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
THURSDAY_NOON = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
MWF_IN: dict[str, object] = {"type": "weekdays", "weekdays": ["mon", "wed", "fri"]}
MWF_MASK = 21

INVALID_SCHEDULES: list[object] = [
    {"type": "weekdays", "weekdays": []},
    {"type": "weekdays"},
    {"type": "weekdays", "weekdays": ["xyz"]},
    {"type": "weekdays", "weekdays": ["mon", "xyz"]},
    {"type": "times_per_week"},
    {"type": "times_per_week", "times_per_week": 0},
    {"type": "times_per_week", "times_per_week": 8},
    {"type": "times_per_week", "times_per_week": -1},
    {"type": "monthly"},
    {},
    "daily",
]
INVALID_IDS = [
    "weekdays-empty",
    "weekdays-missing",
    "weekday-unknown",
    "weekday-one-unknown",
    "times-missing",
    "times-0",
    "times-8",
    "times-negative",
    "type-unknown",
    "type-missing",
    "not-an-object",
]


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


def _read(
    type_: str,
    *,
    weekdays: tuple[str, ...] = (),
    times: int | None = None,
    effective_from: str = TODAY,
) -> dict[str, Any]:
    return {
        "type": type_,
        "weekdays": list(weekdays),
        "times_per_week": times,
        "effective_from": effective_from,
    }


def _ok(resp: Response) -> dict[str, Any]:
    assert resp.status_code in (200, 201), resp.text
    body: dict[str, Any] = resp.json()
    return body


def _post(client: TestClient, schedule: object) -> Response:
    resp: Response = client.post(HABITS, json={"name": "Gym", "schedule": schedule})
    return resp


def _patch(client: TestClient, habit_id: str, schedule: object) -> Response:
    resp: Response = client.patch(f"{HABITS}/{habit_id}", json={"schedule": schedule})
    return resp


def _get(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.get(f"{HABITS}/{habit_id}"))


def _rows(db: Session, habit_id: str) -> list[Schedule]:
    db.expire_all()
    query = select(Schedule).where(Schedule.habit_id == habit_id)
    return sorted(db.exec(query).all(), key=lambda row: row.effective_from)


def _row_values(db: Session, habit_id: str) -> list[tuple[str, int, int | None, date]]:
    return [
        (row.type, row.weekdays, row.times_per_week, row.effective_from)
        for row in _rows(db, habit_id)
    ]


def _count(db: Session, model: type[Habit] | type[Schedule]) -> int:
    db.expire_all()
    return len(db.exec(select(model)).all())


def _check_in_dates(db: Session, habit_id: str) -> list[date]:
    db.expire_all()
    rows = db.exec(select(CheckIn).where(CheckIn.habit_id == habit_id)).all()
    return sorted(row.local_date for row in rows)


def _day_ids(client: TestClient, day: str) -> list[str]:
    body = _ok(client.get(f"{DAYS}/{day}"))
    return [item["habit"]["id"] for item in body["items"]]


def _assert_validation_error(resp: Response) -> None:
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# --- US1 Daily schedule by default (FR-001) -----------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_habit_without_schedule_is_daily_effective_today(
    client: TestClient,
) -> None:
    assert create_habit(client)["schedule"] == _read("daily")


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_explicit_daily_schedule_is_accepted(client: TestClient) -> None:
    assert create_habit(client, schedule={"type": "daily"})["schedule"] == _read("daily")


@pytest.mark.usefixtures("ana_id")
def test_fr001_created_habit_has_exactly_one_daily_schedule_row(
    client: TestClient, db: Session
) -> None:
    habit = create_habit(client)
    assert _row_values(db, habit["id"]) == [("daily", 0, None, date(2026, 9, 26))]


@pytest.mark.usefixtures("ana_id")
def test_fr001_created_weekdays_habit_stores_one_row_with_mask(
    client: TestClient, db: Session
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    assert _row_values(db, habit["id"]) == [("weekdays", MWF_MASK, None, date(2026, 9, 26))]


def _from_list(client: TestClient, habit_id: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = _ok(client.get(HABITS))["items"]
    return next(item for item in items if item["id"] == habit_id)


def _from_patch_name(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.patch(f"{HABITS}/{habit_id}", json={"name": "Gym, renamed"}))


def _from_archive(client: TestClient, habit_id: str) -> dict[str, Any]:
    return _ok(client.post(f"{HABITS}/{habit_id}/archive"))


def _from_archived_list(client: TestClient, habit_id: str) -> dict[str, Any]:
    _from_archive(client, habit_id)
    items: list[dict[str, Any]] = _ok(client.get(HABITS, params={"archived": "true"}))["items"]
    return next(item for item in items if item["id"] == habit_id)


def _from_restore(client: TestClient, habit_id: str) -> dict[str, Any]:
    _from_archive(client, habit_id)
    return _ok(client.post(f"{HABITS}/{habit_id}/restore"))


def _from_reorder(client: TestClient, habit_id: str) -> dict[str, Any]:
    body = _ok(client.put(f"{HABITS}/order", json={"habit_ids": [habit_id]}))
    items: list[dict[str, Any]] = body["items"]
    return next(item for item in items if item["id"] == habit_id)


HABIT_READERS: list[Callable[[TestClient, str], dict[str, Any]]] = [
    _from_list,
    _get,
    _from_patch_name,
    _from_archive,
    _from_archived_list,
    _from_restore,
    _from_reorder,
]
HABIT_READER_IDS = ["get-list", "get-one", "patch", "archive", "archived-list", "restore", "order"]


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("read", HABIT_READERS, ids=HABIT_READER_IDS)
def test_fr001_every_habit_response_includes_schedule(
    client: TestClient, read: Callable[[TestClient, str], dict[str, Any]]
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    expected = _read("weekdays", weekdays=("mon", "wed", "fri"))
    assert habit["schedule"] == expected
    assert read(client, habit["id"])["schedule"] == expected


@pytest.mark.parametrize(
    ("timezone", "now", "local_today"),
    [
        ("Asia/Tokyo", datetime(2026, 9, 26, 22, 30, tzinfo=UTC), "2026-09-27"),
        ("America/Mexico_City", datetime(2026, 9, 29, 4, 30, tzinfo=UTC), "2026-09-28"),
    ],
    ids=["east-of-utc-next-day", "west-of-utc-previous-day"],
)
def test_fr001_effective_from_is_users_local_today(
    client: TestClient, clock: FrozenClock, timezone: str, now: datetime, local_today: str
) -> None:
    clock.set(now)
    register(client, email="ana@example.com", timezone=timezone)
    assert create_habit(client)["schedule"]["effective_from"] == local_today


def test_fr001_migration_0005_backfills_daily_schedule_for_existing_habits(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pre-0005.db"
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    config.attributes["configure_logger"] = False
    command.upgrade(config, "0004")
    engine = build_engine(f"sqlite:///{path}")
    created_at = datetime(2026, 9, 20, 23, 30, tzinfo=UTC)
    with Session(engine) as db:
        user = make_user(db, created_at=created_at)
        # Raw rows: make_habit also writes a schedule, which does not exist before 0005.
        habits = [Habit(user_id=user.id, name=name, created_at=created_at) for name in ("R", "W")]
        db.add_all(habits)
        db.commit()
        habit_ids = {habit.id for habit in habits}
    command.upgrade(config, "head")
    with Session(engine) as db:
        values = {
            (row.habit_id, row.type, row.weekdays, row.times_per_week, row.effective_from)
            for row in db.exec(select(Schedule)).all()
        }
    engine.dispose()
    assert values == {(hid, "daily", 0, None, date(2026, 9, 20)) for hid in habit_ids}


# --- US2 Specific weekdays (FR-002) -------------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us2_s1_fr002_weekdays_returned_monday_first(client: TestClient) -> None:
    habit = create_habit(client, schedule={"type": "weekdays", "weekdays": ["fri", "mon", "wed"]})
    assert habit["schedule"] == _read("weekdays", weekdays=("mon", "wed", "fri"))


@pytest.mark.usefixtures("ana_id")
def test_r2_fr002_duplicate_weekdays_collapse(client: TestClient, db: Session) -> None:
    schedule = {"type": "weekdays", "weekdays": ["wed", "mon", "mon", "wed"]}
    habit = create_habit(client, schedule=schedule)
    assert habit["schedule"]["weekdays"] == ["mon", "wed"]
    assert _rows(db, habit["id"])[0].weekdays == 5


@pytest.mark.usefixtures("ana_id")
def test_fr002_all_seven_weekdays_accepted(client: TestClient) -> None:
    every = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    habit = create_habit(client, schedule={"type": "weekdays", "weekdays": list(reversed(every))})
    assert habit["schedule"] == _read("weekdays", weekdays=every)


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("schedule", INVALID_SCHEDULES, ids=INVALID_IDS)
def test_us2_s2_fr002_invalid_schedule_rejected_and_nothing_saved(
    client: TestClient, db: Session, schedule: object
) -> None:
    _assert_validation_error(_post(client, schedule))
    assert _count(db, Habit) == 0
    assert _count(db, Schedule) == 0


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        ({"type": "daily", "weekdays": ["mon"]}, _read("daily")),
        ({"type": "daily", "times_per_week": 3}, _read("daily")),
        (
            {"type": "weekdays", "weekdays": ["tue"], "times_per_week": 3},
            _read("weekdays", weekdays=("tue",)),
        ),
        (
            {"type": "times_per_week", "times_per_week": 3, "weekdays": ["mon"]},
            _read("times_per_week", times=3),
        ),
    ],
    ids=["daily-with-weekdays", "daily-with-times", "weekdays-with-times", "times-with-weekdays"],
)
def test_r2_fields_irrelevant_to_type_are_ignored(
    client: TestClient, schedule: dict[str, object], expected: dict[str, Any]
) -> None:
    assert create_habit(client, schedule=schedule)["schedule"] == expected


# --- US3 N times per week (FR-003) --------------------------------------------


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("times", [1, 3, 6])
def test_fr003_times_per_week_1_to_6_accepted(client: TestClient, db: Session, times: int) -> None:
    habit = create_habit(client, schedule={"type": "times_per_week", "times_per_week": times})
    assert habit["schedule"] == _read("times_per_week", times=times)
    assert _row_values(db, habit["id"]) == [("times_per_week", 0, times, date(2026, 9, 26))]


@pytest.mark.usefixtures("ana_id")
def test_edge_fr003_seven_times_per_week_is_stored_as_daily(
    client: TestClient, db: Session
) -> None:
    habit = create_habit(client, schedule={"type": "times_per_week", "times_per_week": 7})
    assert habit["schedule"] == _read("daily")
    assert _row_values(db, habit["id"]) == [("daily", 0, None, date(2026, 9, 26))]


# --- US4 Change schedule safely (FR-005, FR-006; research R4) -----------------


@pytest.mark.usefixtures("monday_ana")
def test_us4_s1_fr005_patch_schedule_is_effective_today(
    client: TestClient, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    body = _ok(_patch(client, habit["id"], {"type": "daily"}))
    assert body["schedule"] == _read("daily", effective_from="2026-09-24")
    assert _get(client, habit["id"])["schedule"] == _read("daily", effective_from="2026-09-24")


@pytest.mark.usefixtures("monday_ana")
def test_us4_s1_fr006_schedule_change_keeps_history_row(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    _ok(_patch(client, habit["id"], {"type": "daily"}))
    assert _row_values(db, habit["id"]) == [
        ("weekdays", MWF_MASK, None, date(2026, 9, 21)),
        ("daily", 0, None, date(2026, 9, 24)),
    ]


@pytest.mark.usefixtures("monday_ana")
def test_us4_s1_fr006_past_dates_keep_old_rule(client: TestClient, clock: FrozenClock) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    _ok(_patch(client, habit["id"], {"type": "daily"}))
    assert habit["id"] not in _day_ids(client, "2026-09-22")
    assert habit["id"] in _day_ids(client, "2026-09-23")
    assert habit["id"] in _day_ids(client, "2026-09-24")


@pytest.mark.usefixtures("monday_ana")
def test_r7_day_item_habit_shows_current_schedule_on_past_date(
    client: TestClient, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    _ok(_patch(client, habit["id"], {"type": "daily"}))
    items = _ok(client.get(f"{DAYS}/2026-09-23"))["items"]
    assert [item["habit"]["schedule"] for item in items] == [
        _read("daily", effective_from="2026-09-24")
    ]


@pytest.mark.usefixtures("monday_ana")
def test_r4_same_day_schedule_edits_update_in_place(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    _ok(_patch(client, habit["id"], {"type": "daily"}))
    clock.advance(timedelta(hours=3))
    body = _ok(_patch(client, habit["id"], {"type": "times_per_week", "times_per_week": 3}))
    assert body["schedule"] == _read("times_per_week", times=3, effective_from="2026-09-24")
    assert _row_values(db, habit["id"]) == [
        ("weekdays", MWF_MASK, None, date(2026, 9, 21)),
        ("times_per_week", 0, 3, date(2026, 9, 24)),
    ]


@pytest.mark.usefixtures("ana_id")
def test_r4_edit_on_creation_day_updates_initial_row(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    body = _ok(_patch(client, habit["id"], MWF_IN))
    assert body["schedule"] == _read("weekdays", weekdays=("mon", "wed", "fri"))
    assert _row_values(db, habit["id"]) == [("weekdays", MWF_MASK, None, date(2026, 9, 26))]


@pytest.mark.usefixtures("monday_ana")
def test_r4_patch_with_same_rule_writes_nothing(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    same = {"type": "weekdays", "weekdays": ["fri", "wed", "mon"]}
    body = _ok(_patch(client, habit["id"], same))
    expected = _read("weekdays", weekdays=("mon", "wed", "fri"), effective_from="2026-09-21")
    assert body["schedule"] == expected
    assert _row_values(db, habit["id"]) == [("weekdays", MWF_MASK, None, date(2026, 9, 21))]


@pytest.mark.usefixtures("monday_ana")
def test_r4_patch_without_schedule_keeps_schedule(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    body = _ok(client.patch(f"{HABITS}/{habit['id']}", json={"name": "Gym"}))
    assert body["schedule"] == habit["schedule"]
    assert _row_values(db, habit["id"]) == [("weekdays", MWF_MASK, None, date(2026, 9, 21))]


@pytest.mark.usefixtures("monday_ana")
def test_us4_s1_fr005_schedule_change_keeps_check_ins(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client)
    clock.set(THURSDAY_NOON)
    for day in ("2026-09-21", "2026-09-22", "2026-09-23"):
        check_in(client, habit["id"], day)
    _ok(_patch(client, habit["id"], {"type": "weekdays", "weekdays": ["sat"]}))
    body = _ok(_patch(client, habit["id"], {"type": "times_per_week", "times_per_week": 1}))
    assert body["schedule"]["type"] == "times_per_week"
    assert _check_in_dates(db, habit["id"]) == [
        date(2026, 9, 21),
        date(2026, 9, 22),
        date(2026, 9, 23),
    ]


@pytest.mark.usefixtures("monday_ana")
@pytest.mark.parametrize("schedule", INVALID_SCHEDULES, ids=INVALID_IDS)
def test_fr002_patch_invalid_schedule_rejected_and_unchanged(
    client: TestClient, db: Session, clock: FrozenClock, schedule: object
) -> None:
    habit = create_habit(client, schedule=MWF_IN)
    clock.set(THURSDAY_NOON)
    _assert_validation_error(_patch(client, habit["id"], schedule))
    assert _get(client, habit["id"])["schedule"] == habit["schedule"]
    assert _row_values(db, habit["id"]) == [("weekdays", MWF_MASK, None, date(2026, 9, 21))]


@pytest.mark.usefixtures("ana_id")
def test_fr005_patch_other_users_habit_schedule_is_not_found(
    client: TestClient, other: TestClient, db: Session
) -> None:
    habit = create_habit(client)
    resp = _patch(other, habit["id"], MWF_IN)
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["code"] == "NOT_FOUND"
    assert _row_values(db, habit["id"]) == [("daily", 0, None, date(2026, 9, 26))]
