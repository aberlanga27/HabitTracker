"""Principle V: the committed OpenAPI snapshot must match the running app."""

from scripts.export_openapi import SNAPSHOT, render


def test_openapi_snapshot_is_up_to_date() -> None:
    assert SNAPSHOT.read_text() == render(), (
        "OpenAPI changed. Run `../../.venv/bin/python -m scripts.export_openapi` in src/backend "
        "and `npm run gen:api` in src/frontend."
    )
