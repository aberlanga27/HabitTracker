"""Spec 002 schema rules (research R1-R3): name, description, icon, color."""

from typing import Any

import pydantic
import pytest
from app.schemas.habits import HabitCreate, HabitUpdate

PALETTE = ["coral", "amber", "lime", "teal", "sky", "indigo", "violet", "rose"]


def _create(**fields: object) -> dict[str, Any]:
    payload: dict[str, object] = {"name": "Read 10 pages", **fields}
    dumped: dict[str, Any] = HabitCreate.model_validate(payload).model_dump(mode="json")
    return dumped


# --- name -------------------------------------------------------------------


def test_fr001_name_is_trimmed() -> None:
    assert _create(name="  Read 10 pages  ")["name"] == "Read 10 pages"


def test_fr001_name_of_one_char_accepted() -> None:
    assert _create(name="R")["name"] == "R"


def test_fr001_name_of_80_chars_after_trim_accepted() -> None:
    assert _create(name="  " + "a" * 80 + " ")["name"] == "a" * 80


@pytest.mark.parametrize("name", ["", "   ", "\t\n", "a" * 81], ids=["empty", "spaces", "ws", "81"])
def test_us1_s2_fr001_blank_or_too_long_name_rejected(name: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitCreate.model_validate({"name": name})


def test_fr001_name_is_required() -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitCreate.model_validate({})


# --- description ------------------------------------------------------------


def test_fr001_description_defaults_to_null() -> None:
    assert _create()["description"] is None


def test_fr001_description_is_trimmed() -> None:
    assert _create(description="  Before bed  ")["description"] == "Before bed"


@pytest.mark.parametrize("description", ["", "   "], ids=["empty", "spaces"])
def test_fr001_empty_description_becomes_null(description: str) -> None:
    assert _create(description=description)["description"] is None


def test_fr001_description_of_500_chars_after_trim_accepted() -> None:
    assert _create(description=" " + "d" * 500 + " ")["description"] == "d" * 500


def test_fr001_description_over_500_chars_rejected() -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitCreate.model_validate({"name": "Read", "description": "d" * 501})


# --- icon (R2) --------------------------------------------------------------


def test_fr001_icon_defaults_to_null() -> None:
    assert _create()["icon"] is None


@pytest.mark.parametrize(
    "icon",
    ["📚", "💧", "❤️", "👩‍💻", "🇲🇽", "⭐" * 16],
    ids=["books", "droplet", "variation-selector", "zwj", "flag", "16-chars"],
)
def test_r2_emoji_icon_accepted(icon: str) -> None:
    assert _create(icon=icon)["icon"] == icon


@pytest.mark.parametrize(
    "icon",
    ["", " ", "abc", "A", "7", "📚 x", "📚 📚", "⭐" * 17],
    ids=["empty", "space", "letters", "letter", "digit", "emoji-and-text", "inner-ws", "17-chars"],
)
def test_r2_icon_with_ascii_alnum_whitespace_or_bad_length_rejected(icon: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitCreate.model_validate({"name": "Read", "icon": icon})


# --- color (R1) -------------------------------------------------------------


def test_r1_color_defaults_to_coral() -> None:
    assert _create()["color"] == "coral"


@pytest.mark.parametrize("color", PALETTE)
def test_r1_palette_color_accepted(color: str) -> None:
    assert _create(color=color)["color"] == color


@pytest.mark.parametrize("color", ["red", "#ff7f50", ""], ids=["name", "hex", "empty"])
def test_r1_color_outside_palette_rejected(color: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitCreate.model_validate({"name": "Read", "color": color})


# --- HabitUpdate (FR-002) ---------------------------------------------------


def test_fr002_update_accepts_empty_payload() -> None:
    HabitUpdate.model_validate({})


def test_fr002_update_name_is_trimmed() -> None:
    update = HabitUpdate.model_validate({"name": "  Read 20 pages "})
    assert update.model_dump(mode="json")["name"] == "Read 20 pages"


@pytest.mark.parametrize("name", [None, "", "   ", "a" * 81], ids=["null", "empty", "spaces", "81"])
def test_fr002_update_null_blank_or_too_long_name_rejected(name: str | None) -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitUpdate.model_validate({"name": name})


def test_fr002_update_empty_description_becomes_null() -> None:
    update = HabitUpdate.model_validate({"description": "  "})
    assert update.model_dump(mode="json")["description"] is None


def test_fr002_update_null_description_and_icon_accepted() -> None:
    dumped = HabitUpdate.model_validate({"description": None, "icon": None}).model_dump()
    assert dumped["description"] is None
    assert dumped["icon"] is None


@pytest.mark.parametrize(
    "fields",
    [{"description": "d" * 501}, {"icon": "abc"}, {"icon": "📚 x"}, {"color": "red"}],
    ids=["long-description", "text-icon", "mixed-icon", "bad-color"],
)
def test_fr002_update_applies_same_field_rules_as_create(fields: dict[str, str]) -> None:
    with pytest.raises(pydantic.ValidationError):
        HabitUpdate.model_validate(fields)
