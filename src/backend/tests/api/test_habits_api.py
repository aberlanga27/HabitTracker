"""Spec 002 Habit Management API tests, grouped by user story."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session, select

from app.models import Habit
from tests.factories import create_habit, make_habit, register
from tests.fakes import FrozenClock

BASE = "/api/v1/habits"
NOW_ISO = "2026-09-26T12:00:00Z"
EARLIER = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
UNKNOWN_ID = "00000000-0000-7000-8000-000000000000"
LIMIT_ERROR = {
    "code": "HABIT_LIMIT_REACHED",
    "message": "Habit limit reached (50)",
    "details": {"limit": 50},
}


@pytest.fixture
def ana_id(client: TestClient) -> str:
    """Signs `client` in as Ana and returns her user id."""
    return register(client, email="ana@example.com")["id"]


@pytest.fixture
def other(app: FastAPI) -> Iterator[TestClient]:
    """A second signed-in client for Ben."""
    with TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"}) as other_client:
        register(other_client, email="ben@example.com")
        yield other_client


def _seed(db: Session, user_id: str, *, active: int, archived: int = 0) -> list[Habit]:
    habits = [
        make_habit(db, user_id=user_id, created_at=EARLIER, name=f"Habit {i}", position=i)
        for i in range(active)
    ]
    habits += [
        make_habit(
            db,
            user_id=user_id,
            created_at=EARLIER,
            name=f"Old {i}",
            position=active + i,
            archived_at=EARLIER + timedelta(days=1),
        )
        for i in range(archived)
    ]
    return habits


def _list(client: TestClient, *, archived: bool | None = None) -> dict[str, Any]:
    params = {} if archived is None else {"archived": str(archived).lower()}
    resp = client.get(BASE, params=params)
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _ids(body: dict[str, Any]) -> list[str]:
    return [item["id"] for item in body["items"]]


def _habit_count(db: Session) -> int:
    return len(db.exec(select(Habit)).all())


def _assert_not_found(resp: Response) -> None:
    assert resp.status_code == 404, resp.text
    error = resp.json()["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "Habit not found"


def _assert_validation_error(resp: Response) -> None:
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# --- Authentication -----------------------------------------------------------


def test_habits_list_requires_authentication(client: TestClient) -> None:
    resp = client.get(BASE)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


# --- US1 Create a habit (FR-001, FR-006, FR-007) ------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_create_habit_returns_habit_with_defaults(client: TestClient) -> None:
    resp = client.post(BASE, json={"name": "Read 10 pages"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert isinstance(body["id"], str) and body["id"]
    assert {k: v for k, v in body.items() if k != "id"} == {
        "name": "Read 10 pages",
        "description": None,
        "icon": None,
        "color": "coral",
        "position": 0,
        "archived_at": None,
        "created_at": NOW_ISO,
        "schedule": {
            "type": "daily",
            "weekdays": [],
            "times_per_week": None,
            "effective_from": NOW_ISO[:10],
        },
    }


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_create_habit_is_listed(client: TestClient) -> None:
    created = create_habit(client, name="Read 10 pages")
    body = _list(client)
    assert body["total"] == 1
    assert body["items"] == [created]


@pytest.mark.usefixtures("ana_id")
def test_us1_s1_fr001_create_habit_with_all_fields_persists(client: TestClient) -> None:
    created = create_habit(
        client, name="Drink 2L of water", description="Throughout the day", icon="💧", color="sky"
    )
    assert created["description"] == "Throughout the day"
    assert created["icon"] == "💧"
    assert created["color"] == "sky"
    fetched = client.get(f"{BASE}/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


@pytest.mark.usefixtures("ana_id")
def test_fr001_name_and_description_are_trimmed(client: TestClient) -> None:
    created = create_habit(client, name="  Read 10 pages  ", description="  Before bed ")
    assert created["name"] == "Read 10 pages"
    assert created["description"] == "Before bed"


@pytest.mark.usefixtures("ana_id")
def test_fr001_empty_description_is_stored_as_null(client: TestClient) -> None:
    created = create_habit(client, description="   ")
    assert created["description"] is None


@pytest.mark.usefixtures("ana_id")
def test_fr001_80_char_name_accepted(client: TestClient) -> None:
    assert create_habit(client, name="a" * 80)["name"] == "a" * 80


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("name", ["", "   ", "a" * 81], ids=["empty", "blank", "81-chars"])
def test_us1_s2_fr001_blank_or_too_long_name_rejected_and_nothing_saved(
    client: TestClient, db: Session, name: str
) -> None:
    _assert_validation_error(client.post(BASE, json={"name": name}))
    assert _habit_count(db) == 0


@pytest.mark.usefixtures("ana_id")
def test_fr001_missing_name_rejected(client: TestClient) -> None:
    _assert_validation_error(client.post(BASE, json={"color": "teal"}))


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize(
    "fields",
    [{"description": "d" * 501}, {"icon": "abc"}, {"icon": "📚 x"}, {"color": "red"}],
    ids=["description-501", "text-icon", "mixed-icon", "color-outside-palette"],
)
def test_fr001_invalid_optional_field_rejected(
    client: TestClient, db: Session, fields: dict[str, str]
) -> None:
    _assert_validation_error(client.post(BASE, json={"name": "Read", **fields}))
    assert _habit_count(db) == 0


@pytest.mark.usefixtures("ana_id")
def test_fr001_new_habits_are_appended_to_the_end(client: TestClient) -> None:
    first = create_habit(client, name="A")
    second = create_habit(client, name="B")
    third = create_habit(client, name="C")
    assert [first["position"], second["position"], third["position"]] == [0, 1, 2]
    assert _ids(_list(client)) == [first["id"], second["id"], third["id"]]


def test_fr001_new_habit_position_is_max_plus_one(
    client: TestClient, db: Session, ana_id: str
) -> None:
    make_habit(db, user_id=ana_id, created_at=EARLIER, position=4)
    assert create_habit(client)["position"] == 5


@pytest.mark.usefixtures("ana_id")
def test_edge_duplicate_habit_names_allowed(client: TestClient) -> None:
    first = create_habit(client, name="Walk")
    second = create_habit(client, name="Walk")
    assert first["id"] != second["id"]
    assert _list(client)["total"] == 2


def test_fr001_list_is_ordered_by_position_then_created_at(
    client: TestClient, db: Session, ana_id: str
) -> None:
    last = make_habit(db, user_id=ana_id, created_at=EARLIER, name="Last", position=2)
    tie_later = make_habit(
        db, user_id=ana_id, created_at=EARLIER + timedelta(hours=1), name="Tie later", position=0
    )
    tie_earlier = make_habit(db, user_id=ana_id, created_at=EARLIER, name="Tie early", position=0)
    middle = make_habit(db, user_id=ana_id, created_at=EARLIER, name="Middle", position=1)
    body = _list(client)
    assert body["total"] == 4
    assert _ids(body) == [tie_earlier.id, tie_later.id, middle.id, last.id]


def test_us1_s3_fr006_51st_active_habit_rejected(
    client: TestClient, db: Session, ana_id: str
) -> None:
    _seed(db, ana_id, active=50)
    resp = client.post(BASE, json={"name": "One too many"})
    assert resp.status_code == 409
    assert resp.json()["error"] == LIMIT_ERROR
    assert _habit_count(db) == 50
    assert _list(client)["total"] == 50


def test_fr006_archived_habits_do_not_count_toward_limit(
    client: TestClient, db: Session, ana_id: str
) -> None:
    _seed(db, ana_id, active=49, archived=3)
    created = create_habit(client, name="Fiftieth")
    assert created["archived_at"] is None
    assert _list(client)["total"] == 50


def test_fr006_limit_is_per_user(
    client: TestClient, other: TestClient, db: Session, ana_id: str
) -> None:
    _seed(db, ana_id, active=50)
    assert create_habit(other, name="Ben's first")["position"] == 0


def test_fr007_list_only_shows_own_habits(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client, name="Ana's habit")
    ben_habit = create_habit(other, name="Ben's habit")
    assert _ids(_list(client)) == [ana_habit["id"]]
    assert _ids(_list(other)) == [ben_habit["id"]]
    assert ben_habit["position"] == 0


def test_fr007_other_users_habit_is_not_found(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client)
    _assert_not_found(other.get(f"{BASE}/{ana_habit['id']}"))


@pytest.mark.usefixtures("ana_id")
def test_fr007_unknown_habit_is_not_found(client: TestClient) -> None:
    _assert_not_found(client.get(f"{BASE}/{UNKNOWN_ID}"))


# --- US2 Edit a habit (FR-002, FR-007) ----------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us2_s1_fr002_rename_changes_only_the_name(client: TestClient) -> None:
    created = create_habit(
        client, name="Read 10 pages", description="Fiction", icon="📚", color="teal"
    )
    resp = client.patch(f"{BASE}/{created['id']}", json={"name": "Read 20 pages"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {**created, "name": "Read 20 pages"}
    assert client.get(f"{BASE}/{created['id']}").json() == {**created, "name": "Read 20 pages"}


@pytest.mark.usefixtures("ana_id")
def test_fr002_patch_updates_description_icon_and_color(client: TestClient) -> None:
    created = create_habit(client)
    resp = client.patch(
        f"{BASE}/{created['id']}",
        json={"description": "  Before bed ", "icon": "🌙", "color": "indigo"},
    )
    assert resp.status_code == 200, resp.text
    expected = {**created, "description": "Before bed", "icon": "🌙", "color": "indigo"}
    assert resp.json() == expected
    assert client.get(f"{BASE}/{created['id']}").json() == expected


@pytest.mark.usefixtures("ana_id")
def test_fr002_explicit_null_clears_description_and_icon(client: TestClient) -> None:
    created = create_habit(client, description="Fiction", icon="📚", color="rose")
    resp = client.patch(f"{BASE}/{created['id']}", json={"description": None, "icon": None})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {**created, "description": None, "icon": None}


@pytest.mark.usefixtures("ana_id")
def test_fr002_empty_patch_changes_nothing(client: TestClient) -> None:
    created = create_habit(client, description="Fiction", icon="📚", color="rose")
    resp = client.patch(f"{BASE}/{created['id']}", json={})
    assert resp.status_code == 200, resp.text
    assert resp.json() == created


@pytest.mark.usefixtures("ana_id")
def test_fr002_patch_trims_name(client: TestClient) -> None:
    created = create_habit(client)
    resp = client.patch(f"{BASE}/{created['id']}", json={"name": "  Walk  "})
    assert resp.json()["name"] == "Walk"


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize(
    "fields",
    [
        {"name": None},
        {"name": ""},
        {"name": "   "},
        {"name": "a" * 81},
        {"description": "d" * 501},
        {"icon": "abc"},
        {"color": "red"},
    ],
    ids=["null-name", "empty-name", "blank-name", "long-name", "long-desc", "text-icon", "color"],
)
def test_fr002_invalid_patch_rejected_and_habit_unchanged(
    client: TestClient, fields: dict[str, str | None]
) -> None:
    created = create_habit(client, description="Fiction", icon="📚")
    _assert_validation_error(client.patch(f"{BASE}/{created['id']}", json=fields))
    assert client.get(f"{BASE}/{created['id']}").json() == created


def test_fr007_patch_other_users_habit_is_not_found(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client, name="Read 10 pages")
    _assert_not_found(other.patch(f"{BASE}/{ana_habit['id']}", json={"name": "Hijacked"}))
    assert client.get(f"{BASE}/{ana_habit['id']}").json() == ana_habit


@pytest.mark.usefixtures("ana_id")
def test_fr002_patch_unknown_habit_is_not_found(client: TestClient) -> None:
    _assert_not_found(client.patch(f"{BASE}/{UNKNOWN_ID}", json={"name": "Walk"}))


# --- US3 Archive and restore (FR-003, FR-006, FR-007) --------------------------


@pytest.mark.usefixtures("ana_id")
def test_us3_s1_fr003_archive_sets_archived_at_to_now(client: TestClient) -> None:
    created = create_habit(client)
    resp = client.post(f"{BASE}/{created['id']}/archive")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {**created, "archived_at": NOW_ISO}


@pytest.mark.usefixtures("ana_id")
def test_us3_s1_fr003_archived_habit_leaves_active_list_and_is_listed_as_archived(
    client: TestClient,
) -> None:
    kept = create_habit(client, name="Keep")
    gone = create_habit(client, name="Archive me")
    client.post(f"{BASE}/{gone['id']}/archive")
    active = _list(client, archived=False)
    assert _ids(active) == [kept["id"]]
    assert active["total"] == 1
    assert _ids(_list(client)) == [kept["id"]]
    archived = _list(client, archived=True)
    assert _ids(archived) == [gone["id"]]
    assert archived["total"] == 1


@pytest.mark.usefixtures("ana_id")
def test_fr003_archived_habit_is_still_retrievable_by_id(client: TestClient) -> None:
    created = create_habit(client)
    client.post(f"{BASE}/{created['id']}/archive")
    resp = client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["archived_at"] == NOW_ISO


@pytest.mark.usefixtures("ana_id")
def test_fr003_archive_is_idempotent_and_keeps_first_timestamp(
    client: TestClient, clock: FrozenClock
) -> None:
    created = create_habit(client)
    client.post(f"{BASE}/{created['id']}/archive")
    clock.advance(timedelta(days=1))
    resp = client.post(f"{BASE}/{created['id']}/archive")
    assert resp.status_code == 200, resp.text
    assert resp.json()["archived_at"] == NOW_ISO


@pytest.mark.usefixtures("ana_id")
def test_us3_s2_fr003_restore_clears_archived_at_and_appends(
    client: TestClient, clock: FrozenClock
) -> None:
    first = create_habit(client, name="A")
    second = create_habit(client, name="B")
    third = create_habit(client, name="C")
    client.post(f"{BASE}/{first['id']}/archive")
    clock.advance(timedelta(days=2))
    resp = client.post(f"{BASE}/{first['id']}/restore")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {**first, "archived_at": None, "position": 3}
    assert _ids(_list(client)) == [second["id"], third["id"], first["id"]]
    assert _list(client, archived=True)["total"] == 0


@pytest.mark.usefixtures("ana_id")
def test_fr003_restore_is_idempotent(client: TestClient) -> None:
    first = create_habit(client, name="A")
    create_habit(client, name="B")
    client.post(f"{BASE}/{first['id']}/archive")
    restored = client.post(f"{BASE}/{first['id']}/restore").json()
    again = client.post(f"{BASE}/{first['id']}/restore")
    assert again.status_code == 200, again.text
    assert again.json() == restored
    assert again.json()["position"] == 2


@pytest.mark.usefixtures("ana_id")
def test_fr003_restore_of_active_habit_leaves_it_unchanged(client: TestClient) -> None:
    first = create_habit(client, name="A")
    create_habit(client, name="B")
    resp = client.post(f"{BASE}/{first['id']}/restore")
    assert resp.status_code == 200, resp.text
    assert resp.json() == first


def test_fr006_restore_with_50_active_habits_rejected(
    client: TestClient, db: Session, ana_id: str
) -> None:
    archived = _seed(db, ana_id, active=50, archived=1)[-1]
    resp = client.post(f"{BASE}/{archived.id}/restore")
    assert resp.status_code == 409
    assert resp.json()["error"] == LIMIT_ERROR
    assert client.get(f"{BASE}/{archived.id}").json()["archived_at"] is not None
    assert _list(client)["total"] == 50


def test_fr007_archive_other_users_habit_is_not_found(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client)
    _assert_not_found(other.post(f"{BASE}/{ana_habit['id']}/archive"))
    assert client.get(f"{BASE}/{ana_habit['id']}").json()["archived_at"] is None


def test_fr007_restore_other_users_habit_is_not_found(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client)
    client.post(f"{BASE}/{ana_habit['id']}/archive")
    _assert_not_found(other.post(f"{BASE}/{ana_habit['id']}/restore"))
    assert client.get(f"{BASE}/{ana_habit['id']}").json()["archived_at"] == NOW_ISO


@pytest.mark.usefixtures("ana_id")
@pytest.mark.parametrize("action", ["archive", "restore"])
def test_fr003_archive_or_restore_unknown_habit_is_not_found(
    client: TestClient, action: str
) -> None:
    _assert_not_found(client.post(f"{BASE}/{UNKNOWN_ID}/{action}"))


# --- US4 Delete a habit (FR-004, FR-007) --------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us4_s1_fr004_delete_removes_habit_permanently(client: TestClient, db: Session) -> None:
    created = create_habit(client)
    resp = client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 204
    assert resp.content == b""
    _assert_not_found(client.get(f"{BASE}/{created['id']}"))
    assert _list(client)["total"] == 0
    assert _habit_count(db) == 0


def test_fr004_delete_archived_habit(client: TestClient, db: Session, ana_id: str) -> None:
    archived = _seed(db, ana_id, active=0, archived=1)[0]
    assert client.delete(f"{BASE}/{archived.id}").status_code == 204
    assert _list(client, archived=True)["total"] == 0


@pytest.mark.usefixtures("ana_id")
def test_fr004_delete_twice_is_not_found(client: TestClient) -> None:
    created = create_habit(client)
    client.delete(f"{BASE}/{created['id']}")
    _assert_not_found(client.delete(f"{BASE}/{created['id']}"))


def test_fr007_delete_other_users_habit_is_not_found_and_kept(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_habit = create_habit(client)
    _assert_not_found(other.delete(f"{BASE}/{ana_habit['id']}"))
    resp = client.get(f"{BASE}/{ana_habit['id']}")
    assert resp.status_code == 200
    assert resp.json() == ana_habit


# --- US5 Reorder habits (FR-005, FR-007) --------------------------------------


@pytest.mark.usefixtures("ana_id")
def test_us5_s1_fr005_move_third_to_top_is_saved_and_persists(client: TestClient) -> None:
    first = create_habit(client, name="A")
    second = create_habit(client, name="B")
    third = create_habit(client, name="C")
    new_order = [third["id"], first["id"], second["id"]]
    resp = client.put(f"{BASE}/order", json={"habit_ids": new_order})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert _ids(body) == new_order
    assert [item["position"] for item in body["items"]] == [0, 1, 2]
    assert body["total"] == 3
    reloaded = _list(client)
    assert _ids(reloaded) == new_order
    assert [item["position"] for item in reloaded["items"]] == [0, 1, 2]


def test_fr005_reorder_returns_only_active_habits(
    client: TestClient, db: Session, ana_id: str
) -> None:
    first, second, archived = _seed(db, ana_id, active=2, archived=1)
    resp = client.put(f"{BASE}/order", json={"habit_ids": [second.id, first.id]})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == [second.id, first.id]
    assert _ids(_list(client, archived=True)) == [archived.id]


@pytest.mark.parametrize("case", ["missing", "unknown", "duplicate", "archived", "empty"])
def test_fr005_reorder_not_exactly_active_set_rejected(
    client: TestClient, db: Session, ana_id: str, case: str
) -> None:
    first, second, third, archived = _seed(db, ana_id, active=3, archived=1)
    active = [first.id, second.id, third.id]
    habit_ids = {
        "missing": [third.id, first.id],
        "unknown": [third.id, first.id, second.id, UNKNOWN_ID],
        "duplicate": [third.id, first.id, second.id, second.id],
        "archived": [third.id, first.id, second.id, archived.id],
        "empty": [],
    }[case]
    _assert_validation_error(client.put(f"{BASE}/order", json={"habit_ids": habit_ids}))
    assert _ids(_list(client)) == active


@pytest.mark.usefixtures("ana_id")
def test_fr005_reorder_without_habit_ids_rejected(client: TestClient) -> None:
    create_habit(client)
    _assert_validation_error(client.put(f"{BASE}/order", json={}))


def test_fr007_reorder_with_other_users_habit_ids_rejected(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    ana_first = create_habit(client, name="A")
    ana_second = create_habit(client, name="B")
    ben_habit = create_habit(other, name="Ben's")
    resp = client.put(
        f"{BASE}/order", json={"habit_ids": [ana_second["id"], ben_habit["id"], ana_first["id"]]}
    )
    _assert_validation_error(resp)
    assert _ids(_list(client)) == [ana_first["id"], ana_second["id"]]
    assert _list(other)["items"] == [ben_habit]


def test_fr007_reorder_with_only_other_users_ids_rejected(
    client: TestClient, other: TestClient, ana_id: str
) -> None:
    create_habit(client, name="A")
    ben_first = create_habit(other, name="Ben 1")
    ben_second = create_habit(other, name="Ben 2")
    resp = client.put(f"{BASE}/order", json={"habit_ids": [ben_second["id"], ben_first["id"]]})
    _assert_validation_error(resp)
    assert _ids(_list(other)) == [ben_first["id"], ben_second["id"]]
