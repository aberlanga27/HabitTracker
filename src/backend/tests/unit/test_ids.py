import uuid

from app.core.ids import new_id


def test_new_id_is_uuid_version_7() -> None:
    assert uuid.UUID(new_id()).version == 7


def test_new_ids_are_unique_and_time_ordered() -> None:
    ids = [new_id() for _ in range(200)]
    assert len(set(ids)) == len(ids)
    assert ids == sorted(ids)
