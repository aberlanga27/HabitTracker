"""Spec 003 Daily Check-In API tests, grouped by user story."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session, select

from app.models import CheckIn
from tests.factories import check_in, create_habit, make_check_in, register
from tests.fakes import FrozenClock

HABITS = "/api/v1/habits"
LIST = "/api/v1/check-ins"
TODAY = "2026-09-26"
YESTERDAY = "2026-09-25"
EARLIEST = "2026-08-27"
NOW_ISO = "2026-09-26T12:00:00Z"
UNKNOWN_ID = "00000000-0000-7000-8000-000000000000"
NOTE_280 = "n" * 280


@pytest.fixture
def ana_id(client: TestClient) -> str:
    """Signs `client` in as Ana (UTC) and returns her user id."""
    return register(client, email="ana@example.com")["id"]


@pytest.fixture
def other(app: FastAPI) -> Iterator[TestClient]:
    """A second signed-in client for Ben."""
    with TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"}) as other_client:
        register(other_client, email="ben@example.com")
        yield other_client


def _put(client: TestClient, habit_id: str, day: str, **body: object) -> Response:
    resp: Response = client.put(f"{HABITS}/{habit_id}/check-ins/{day}", json=body)
    return resp


def _list(client: TestClient, day: str) -> dict[str, Any]:
    resp = client.get(LIST, params={"date": day})
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _rows(db: Session, habit_id: str) -> list[CheckIn]:
    db.expire_all()
    return list(db.exec(select(CheckIn).where(CheckIn.habit_id == habit_id)).all())


def _done(
    habit_id: str, day: str, *, completed_at: str = NOW_ISO, note: str | None = None
) -> dict[str, Any]:
    return {
        "habit_id": habit_id,
        "date": day,
        "completed": True,
        "note": note,
        "completed_at": completed_at,
    }


def _undone(habit_id: str, day: str) -> dict[str, Any]:
    return {
        "habit_id": habit_id,
        "date": day,
        "completed": False,
        "note": None,
        "completed_at": None,
    }


def _assert_habit_not_found(resp: Response) -> None:
    assert resp.status_code == 404, resp.text
    error = resp.json()["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "Habit not found"


def _assert_validation_error(resp: Response) -> None:
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def _assert_out_of_range(resp: Response, *, earliest: str, latest: str) -> None:
    assert resp.status_code == 422, resp.text
    error = resp.json()["error"]
    assert error["code"] == "DATE_OUT_OF_RANGE"
    assert error["details"] == {"earliest": earliest, "latest": latest}


def _assert_archived(resp: Response) -> None:
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"]["code"] == "HABIT_ARCHIVED"


# --- Authentication -----------------------------------------------------------


def test_put_check_in_requires_authentication(client: TestClient) -> None:
    resp = _put(client, UNKNOWN_ID, TODAY, completed=True)
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_list_check_ins_requires_authentication(client: TestClient) -> None:
    resp = client.get(LIST, params={"date": TODAY})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


# --- US1 Check in for today (FR-001, FR-004, FR-007) --------------------------


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_tap_marks_complete(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    resp = _put(client, habit["id"], TODAY, completed=True)
    assert resp.status_code == 200, resp.text
    assert resp.json() == _done(habit["id"], TODAY)
    rows = _rows(db, habit["id"])
    assert [(row.local_date, row.note) for row in rows] == [(date(2026, 9, 26), None)]


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_completion_persists_and_is_listed(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    assert _list(client, TODAY) == {"items": [_done(habit["id"], TODAY)], "total": 1}


@pytest.mark.usefixtures("ana_id")
def test_us1_s2_fr001_tap_completed_habit_undoes_it(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    resp = _put(client, habit["id"], TODAY, completed=False)
    assert resp.status_code == 200, resp.text
    assert resp.json() == _undone(habit["id"], TODAY)
    assert _rows(db, habit["id"]) == []
    assert _list(client, TODAY) == {"items": [], "total": 0}


@pytest.mark.usefixtures("ana_id")
def test_fr001_undo_without_check_in_is_harmless(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    resp = _put(client, habit["id"], TODAY, completed=False)
    assert resp.status_code == 200, resp.text
    assert resp.json() == _undone(habit["id"], TODAY)
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
def test_fr001_redo_after_undo_records_new_completed_at(
    client: TestClient, clock: FrozenClock
) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    check_in(client, habit["id"], TODAY, completed=False)
    clock.advance(timedelta(hours=1))
    body = check_in(client, habit["id"], TODAY)
    assert body == _done(habit["id"], TODAY, completed_at="2026-09-26T13:00:00Z")


@pytest.mark.usefixtures("ana_id")
def test_fr004_repeat_put_keeps_one_row_and_original_completed_at(
    client: TestClient, db: Session, clock: FrozenClock
) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    clock.advance(timedelta(hours=1))
    assert check_in(client, habit["id"], TODAY) == _done(habit["id"], TODAY)
    assert len(_rows(db, habit["id"])) == 1


@pytest.mark.usefixtures("ana_id")
def test_fr004_put_over_seeded_row_keeps_it(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    seeded_at = datetime(2026, 9, 26, 7, 15, tzinfo=UTC)
    seeded = make_check_in(
        db, habit_id=habit["id"], local_date=date(2026, 9, 26), completed_at=seeded_at
    )
    body = check_in(client, habit["id"], TODAY)
    assert body == _done(habit["id"], TODAY, completed_at="2026-09-26T07:15:00Z")
    assert [row.id for row in _rows(db, habit["id"])] == [seeded.id]


@pytest.mark.usefixtures("ana_id")
def test_sc002_twenty_rapid_puts_create_one_row(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    responses = [_put(client, habit["id"], TODAY, completed=True) for _ in range(20)]
    assert [resp.status_code for resp in responses] == [200] * 20
    assert all(resp.json() == _done(habit["id"], TODAY) for resp in responses)
    assert len(_rows(db, habit["id"])) == 1


@pytest.mark.usefixtures("ana_id")
def test_fr001_missing_completed_is_validation_error(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    _assert_validation_error(_put(client, habit["id"], TODAY))
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", ["2026-13-01", "2026-02-30", "yesterday"])
def test_fr001_malformed_date_is_validation_error(client: TestClient, day: str) -> None:
    habit = create_habit(client)
    _assert_validation_error(_put(client, habit["id"], day, completed=True))


@pytest.mark.usefixtures("ana_id")
def test_fr001_list_returns_only_check_ins_on_that_date(client: TestClient) -> None:
    read = create_habit(client, name="Read")
    walk = create_habit(client, name="Walk")
    stretch = create_habit(client, name="Stretch")
    check_in(client, read["id"], TODAY)
    check_in(client, walk["id"], TODAY)
    check_in(client, stretch["id"], YESTERDAY)
    today = _list(client, TODAY)
    assert today["total"] == 2
    expected = [_done(read["id"], TODAY), _done(walk["id"], TODAY)]
    assert sorted(today["items"], key=lambda item: item["habit_id"]) == sorted(
        expected, key=lambda item: item["habit_id"]
    )
    assert _list(client, YESTERDAY) == {"items": [_done(stretch["id"], YESTERDAY)], "total": 1}


@pytest.mark.usefixtures("ana_id")
def test_fr001_list_excludes_other_users_check_ins(client: TestClient, other: TestClient) -> None:
    ana_habit = create_habit(client, name="Ana's habit")
    ben_habit = create_habit(other, name="Ben's habit")
    check_in(client, ana_habit["id"], TODAY)
    check_in(other, ben_habit["id"], TODAY)
    assert _list(client, TODAY) == {"items": [_done(ana_habit["id"], TODAY)], "total": 1}
    assert _list(other, TODAY) == {"items": [_done(ben_habit["id"], TODAY)], "total": 1}


@pytest.mark.usefixtures("ana_id")
def test_fr001_list_requires_date_param(client: TestClient) -> None:
    _assert_validation_error(client.get(LIST))


@pytest.mark.usefixtures("ana_id")
def test_fr001_list_rejects_malformed_date(client: TestClient) -> None:
    _assert_validation_error(client.get(LIST, params={"date": "2026-13-01"}))


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("completed", [True, False], ids=["complete", "undo"])
def test_fr001_other_users_habit_is_not_found(
    client: TestClient, other: TestClient, db: Session, completed: bool
) -> None:
    ana_habit = create_habit(client)
    check_in(client, ana_habit["id"], YESTERDAY)
    _assert_habit_not_found(_put(other, ana_habit["id"], YESTERDAY, completed=completed))
    _assert_habit_not_found(_put(other, ana_habit["id"], TODAY, completed=completed))
    assert [row.local_date for row in _rows(db, ana_habit["id"])] == [date(2026, 9, 25)]


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("completed", [True, False], ids=["complete", "undo"])
def test_fr001_unknown_habit_is_not_found(client: TestClient, completed: bool) -> None:
    _assert_habit_not_found(_put(client, UNKNOWN_ID, TODAY, completed=completed))


@pytest.mark.usefixtures("ana_id")
def test_edge_archived_habit_rejects_new_check_in(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    assert client.post(f"{HABITS}/{habit['id']}/archive").status_code == 200
    _assert_archived(_put(client, habit["id"], TODAY, completed=True))
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
def test_edge_archived_habit_rejects_undo_and_keeps_check_in(
    client: TestClient, db: Session
) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    assert client.post(f"{HABITS}/{habit['id']}/archive").status_code == 200
    _assert_archived(_put(client, habit["id"], TODAY, completed=False))
    assert len(_rows(db, habit["id"])) == 1


@pytest.mark.usefixtures("ana_id")
def test_edge_archived_habit_rejects_note_edit(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="before archive")
    assert client.post(f"{HABITS}/{habit['id']}/archive").status_code == 200
    _assert_archived(_put(client, habit["id"], TODAY, completed=True, note="after archive"))


# --- FR-007 "today" is the user's local date ----------------------------------


@dataclass(frozen=True)
class LocalDay:
    timezone: str
    now: datetime
    today: str
    tomorrow: str
    earliest: str
    before_earliest: str


LOCAL_DAYS = [
    LocalDay(
        "America/Mexico_City",
        datetime(2026, 9, 27, 5, 59, tzinfo=UTC),
        "2026-09-26",
        "2026-09-27",
        "2026-08-27",
        "2026-08-26",
    ),
    LocalDay(
        "Asia/Tokyo",
        datetime(2026, 9, 26, 22, 30, tzinfo=UTC),
        "2026-09-27",
        "2026-09-28",
        "2026-08-28",
        "2026-08-27",
    ),
    LocalDay(
        "Europe/Madrid",
        datetime(2026, 3, 29, 21, 59, tzinfo=UTC),
        "2026-03-29",
        "2026-03-30",
        "2026-02-27",
        "2026-02-26",
    ),
    LocalDay(
        "Europe/Madrid",
        datetime(2026, 10, 25, 22, 59, tzinfo=UTC),
        "2026-10-25",
        "2026-10-26",
        "2026-09-25",
        "2026-09-24",
    ),
]
LOCAL_DAY_IDS = [
    "west-of-utc-2359-local",
    "east-of-utc-next-utc-day",
    "dst-spring-forward-2359-local",
    "dst-fall-back-2359-local",
]


def _sign_in_at(client: TestClient, clock: FrozenClock, case: LocalDay) -> str:
    clock.set(case.now)
    register(client, email="ana@example.com", timezone=case.timezone)
    habit_id: str = create_habit(client)["id"]
    return habit_id


@pytest.mark.parametrize("case", LOCAL_DAYS, ids=LOCAL_DAY_IDS)
def test_fr007_2359_local_counts_for_local_date(
    client: TestClient, clock: FrozenClock, case: LocalDay
) -> None:
    habit_id = _sign_in_at(client, clock, case)
    body = check_in(client, habit_id, case.today)
    completed_at = case.now.isoformat().replace("+00:00", "Z")
    assert body == _done(habit_id, case.today, completed_at=completed_at)
    assert _list(client, case.today)["total"] == 1


@pytest.mark.parametrize("case", LOCAL_DAYS, ids=LOCAL_DAY_IDS)
def test_fr007_next_local_date_is_future(
    client: TestClient, clock: FrozenClock, case: LocalDay
) -> None:
    habit_id = _sign_in_at(client, clock, case)
    resp = _put(client, habit_id, case.tomorrow, completed=True)
    _assert_out_of_range(resp, earliest=case.earliest, latest=case.today)


@pytest.mark.parametrize("case", LOCAL_DAYS, ids=LOCAL_DAY_IDS)
def test_fr007_window_earliest_follows_user_timezone(
    client: TestClient, clock: FrozenClock, case: LocalDay
) -> None:
    habit_id = _sign_in_at(client, clock, case)
    assert check_in(client, habit_id, case.earliest)["date"] == case.earliest
    resp = _put(client, habit_id, case.before_earliest, completed=True)
    _assert_out_of_range(resp, earliest=case.earliest, latest=case.today)


# --- US2 Backfill a past day (FR-002, FR-003) ---------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us2_s1_fr002_backfill_yesterday_is_stored(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    assert check_in(client, habit["id"], YESTERDAY) == _done(habit["id"], YESTERDAY)
    assert [row.local_date for row in _rows(db, habit["id"])] == [date(2026, 9, 25)]
    assert _list(client, YESTERDAY) == {"items": [_done(habit["id"], YESTERDAY)], "total": 1}
    assert _list(client, TODAY) == {"items": [], "total": 0}


@pytest.mark.usefixtures("ana_id")
def test_fr002_today_minus_30_is_accepted(client: TestClient) -> None:
    habit = create_habit(client)
    assert check_in(client, habit["id"], EARLIEST) == _done(habit["id"], EARLIEST)


@pytest.mark.usefixtures("ana_id")
def test_fr002_undo_backfilled_day(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], EARLIEST)
    assert check_in(client, habit["id"], EARLIEST, completed=False) == _undone(
        habit["id"], EARLIEST
    )
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", ["2026-08-26", "2025-09-26"], ids=["today-31", "last-year"])
def test_us2_s2_fr003_older_than_30_days_rejected(
    client: TestClient, db: Session, day: str
) -> None:
    habit = create_habit(client)
    _assert_out_of_range(
        _put(client, habit["id"], day, completed=True), earliest=EARLIEST, latest=TODAY
    )
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("day", ["2026-09-27", "2027-01-01"], ids=["tomorrow", "next-year"])
def test_us2_s3_fr003_future_date_rejected(client: TestClient, db: Session, day: str) -> None:
    habit = create_habit(client)
    _assert_out_of_range(
        _put(client, habit["id"], day, completed=True), earliest=EARLIEST, latest=TODAY
    )
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
def test_fr003_undo_older_than_30_days_rejected_and_row_kept(
    client: TestClient, db: Session
) -> None:
    habit = create_habit(client)
    make_check_in(
        db,
        habit_id=habit["id"],
        local_date=date(2026, 8, 1),
        completed_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    )
    resp = _put(client, habit["id"], "2026-08-01", completed=False)
    _assert_out_of_range(resp, earliest=EARLIEST, latest=TODAY)
    assert len(_rows(db, habit["id"])) == 1


@pytest.mark.usefixtures("ana_id")
def test_fr003_window_moves_forward_with_the_clock(client: TestClient, clock: FrozenClock) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], EARLIEST)
    clock.advance(timedelta(days=1))
    resp = _put(client, habit["id"], EARLIEST, completed=False)
    _assert_out_of_range(resp, earliest="2026-08-28", latest="2026-09-27")
    assert check_in(client, habit["id"], "2026-09-27")["date"] == "2026-09-27"


# --- US3 Add a note (FR-005) ---------------------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us3_s1_fr005_note_is_saved_and_visible_on_that_day(client: TestClient) -> None:
    habit = create_habit(client)
    body = check_in(client, habit["id"], TODAY, note="ran 5k in the rain")
    expected = _done(habit["id"], TODAY, note="ran 5k in the rain")
    assert body == expected
    assert _list(client, TODAY) == {"items": [expected], "total": 1}


@pytest.mark.usefixtures("ana_id")
def test_fr005_note_added_to_existing_check_in_keeps_completed_at(
    client: TestClient, clock: FrozenClock
) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY)
    clock.advance(timedelta(minutes=5))
    body = check_in(client, habit["id"], TODAY, note="ran 5k")
    assert body == _done(habit["id"], TODAY, note="ran 5k")


@pytest.mark.usefixtures("ana_id")
def test_fr005_280_char_note_accepted(client: TestClient) -> None:
    habit = create_habit(client)
    assert check_in(client, habit["id"], TODAY, note=NOTE_280)["note"] == NOTE_280


@pytest.mark.usefixtures("ana_id")
def test_fr005_281_char_note_rejected_and_nothing_saved(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    _assert_validation_error(_put(client, habit["id"], TODAY, completed=True, note="n" * 281))
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
def test_fr005_281_char_note_leaves_existing_note_unchanged(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="keep me")
    _assert_validation_error(_put(client, habit["id"], TODAY, completed=True, note="n" * 281))
    assert _list(client, TODAY)["items"] == [_done(habit["id"], TODAY, note="keep me")]


@pytest.mark.usefixtures("ana_id")
def test_fr005_note_is_trimmed(client: TestClient) -> None:
    habit = create_habit(client)
    assert check_in(client, habit["id"], TODAY, note="  ran 5k \n")["note"] == "ran 5k"


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("note", ["", "   ", "\t\n"], ids=["empty", "spaces", "whitespace"])
def test_fr005_blank_note_is_stored_as_null(client: TestClient, note: str) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="old note")
    assert check_in(client, habit["id"], TODAY, note=note)["note"] is None
    assert _list(client, TODAY)["items"][0]["note"] is None


@pytest.mark.usefixtures("ana_id")
def test_fr005_omitted_note_keeps_existing(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="ran 5k")
    assert check_in(client, habit["id"], TODAY)["note"] == "ran 5k"
    assert _list(client, TODAY)["items"][0]["note"] == "ran 5k"


@pytest.mark.usefixtures("ana_id")
def test_fr005_explicit_null_clears_note(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="ran 5k")
    assert check_in(client, habit["id"], TODAY, note=None) == _done(habit["id"], TODAY)
    assert _list(client, TODAY)["items"][0]["note"] is None


@pytest.mark.usefixtures("ana_id")
def test_fr005_note_ignored_when_undoing(client: TestClient, db: Session) -> None:
    habit = create_habit(client)
    body = check_in(client, habit["id"], TODAY, completed=False, note="never saved")
    assert body == _undone(habit["id"], TODAY)
    assert _rows(db, habit["id"]) == []


@pytest.mark.usefixtures("ana_id")
def test_fr005_undo_discards_note(client: TestClient) -> None:
    habit = create_habit(client)
    check_in(client, habit["id"], TODAY, note="ran 5k")
    check_in(client, habit["id"], TODAY, completed=False)
    assert check_in(client, habit["id"], TODAY)["note"] is None


# --- Spec 002 interplay (002 SC-002, 002 FR-004) -------------------------------


@pytest.mark.usefixtures("ana_id")
def test_s002_sc002_rename_keeps_check_ins(client: TestClient) -> None:
    habit = create_habit(client, name="Read 10 pages")
    check_in(client, habit["id"], TODAY)
    check_in(client, habit["id"], YESTERDAY, note="chapter 3")
    resp = client.patch(f"{HABITS}/{habit['id']}", json={"name": "Read 20 pages"})
    assert resp.status_code == 200, resp.text
    assert _list(client, TODAY)["items"] == [_done(habit["id"], TODAY)]
    assert _list(client, YESTERDAY)["items"] == [_done(habit["id"], YESTERDAY, note="chapter 3")]


@pytest.mark.usefixtures("ana_id")
def test_s002_fr004_delete_habit_removes_its_check_ins(client: TestClient, db: Session) -> None:
    doomed = create_habit(client, name="Doomed")
    kept = create_habit(client, name="Kept")
    check_in(client, doomed["id"], TODAY)
    check_in(client, doomed["id"], YESTERDAY)
    check_in(client, kept["id"], TODAY)
    assert client.delete(f"{HABITS}/{doomed['id']}").status_code == 204
    assert _rows(db, doomed["id"]) == []
    assert len(_rows(db, kept["id"])) == 1
    assert _list(client, TODAY) == {"items": [_done(kept["id"], TODAY)], "total": 1}
