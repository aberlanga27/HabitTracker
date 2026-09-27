"""Spec 006 day summary counts: GET /api/v1/days/{date} (FR-001, FR-002, FR-005)."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from tests.factories import check_in, create_habit, register
from tests.fakes import FrozenClock

TODAY = "2026-09-26"  # Saturday


def _day(client: TestClient, day: str = TODAY) -> dict[str, object]:
    resp = client.get(f"/api/v1/days/{day}")
    assert resp.status_code == 200, resp.text
    body: dict[str, object] = resp.json()
    return body


def _counts(body: dict[str, object]) -> tuple[object, object, object]:
    return body["due_count"], body["completed_count"], body["habit_count"]


def test_us1_s2_fr005_zero_habits_has_zero_counts(client: TestClient) -> None:
    register(client)
    assert _counts(_day(client)) == (0, 0, 0)


def test_us1_s1_fr002_five_due_three_done(client: TestClient) -> None:
    register(client)
    ids = [create_habit(client, name=f"Habit {n}")["id"] for n in range(5)]
    for habit_id in ids[:3]:
        check_in(client, habit_id, TODAY)
    assert _counts(_day(client)) == (5, 3, 5)


def test_us1_s3_fr005_all_done_when_every_due_habit_completed(client: TestClient) -> None:
    register(client)
    ids = [create_habit(client, name=f"Habit {n}")["id"] for n in range(2)]
    for habit_id in ids:
        check_in(client, habit_id, TODAY)
    due, completed, _ = _counts(_day(client))
    assert due == completed == 2


def test_fr001_unscheduled_habits_count_toward_habit_count_only(client: TestClient) -> None:
    register(client)
    create_habit(client, name="Daily")
    create_habit(client, name="Gym", schedule={"type": "weekdays", "weekdays": ["mon"]})
    body = _day(client)
    assert _counts(body) == (1, 0, 2)
    assert len(body["items"]) == 1  # type: ignore[arg-type]


def test_fr002_done_for_week_is_listed_but_not_counted_as_due(
    client: TestClient, clock: FrozenClock
) -> None:
    clock.set(datetime(2026, 9, 21, 12, tzinfo=UTC))  # Monday
    register(client)
    habit_id = create_habit(client, schedule={"type": "times_per_week", "times_per_week": 2})["id"]
    check_in(client, habit_id, "2026-09-21")
    clock.set(datetime(2026, 9, 22, 12, tzinfo=UTC))
    check_in(client, habit_id, "2026-09-22")
    clock.set(datetime(2026, 9, 23, 12, tzinfo=UTC))
    body = _day(client, "2026-09-23")
    assert _counts(body) == (0, 0, 1)
    assert body["items"][0]["status"] == "done_for_week"  # type: ignore[index]


def test_fr002_extra_check_in_on_done_for_week_day_is_not_counted(
    client: TestClient, clock: FrozenClock
) -> None:
    clock.set(datetime(2026, 9, 23, 12, tzinfo=UTC))  # Wednesday
    register(client)
    habit_id = create_habit(client, schedule={"type": "times_per_week", "times_per_week": 1})["id"]
    check_in(client, habit_id, "2026-09-22")
    check_in(client, habit_id, "2026-09-23")
    assert _counts(_day(client, "2026-09-23")) == (0, 0, 1)


def test_fr005_archived_habits_are_not_counted(client: TestClient) -> None:
    register(client)
    create_habit(client, name="Active")
    archived = create_habit(client, name="Old")["id"]
    client.post(f"/api/v1/habits/{archived}/archive")
    assert _counts(_day(client)) == (1, 0, 1)


def test_fr002_counts_are_per_date(client: TestClient) -> None:
    register(client)
    habit_id = create_habit(client)["id"]
    check_in(client, habit_id, "2026-09-25")
    assert _counts(_day(client, "2026-09-25")) == (1, 1, 1)
    assert _counts(_day(client, TODAY)) == (1, 0, 1)
