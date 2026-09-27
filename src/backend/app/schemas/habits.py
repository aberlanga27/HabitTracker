from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    StringConstraints,
    field_validator,
)

from app.schemas.schedules import ScheduleIn, ScheduleRead

HabitColor = Literal["coral", "amber", "lime", "teal", "sky", "indigo", "violet", "rose"]

MAX_DESCRIPTION = 500
MAX_ICON = 16


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _description(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if len(value) > MAX_DESCRIPTION:
        raise ValueError(f"must be at most {MAX_DESCRIPTION} characters")
    return value


def _icon(value: str | None) -> str | None:
    if value is None:
        return None
    if not 1 <= len(value) <= MAX_ICON:
        raise ValueError(f"must be 1 to {MAX_ICON} characters")
    if any(char.isspace() or (char.isascii() and char.isalnum()) for char in value):
        raise ValueError("must be an emoji")
    return value


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Description = Annotated[str | None, BeforeValidator(_strip), AfterValidator(_description)]
Icon = Annotated[str | None, AfterValidator(_icon)]


class HabitCreate(BaseModel):
    name: Name
    description: Description = None
    icon: Icon = None
    color: HabitColor = "coral"
    schedule: ScheduleIn = Field(default_factory=lambda: ScheduleIn(type="daily"))


class HabitUpdate(BaseModel):
    """Partial update; omitted fields are unchanged, null clears description or icon."""

    name: Name | None = None
    description: Description = None
    icon: Icon = None
    color: HabitColor | None = None
    schedule: ScheduleIn | None = None

    @field_validator("name", "color", "schedule")
    @classmethod
    def _not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("may not be null")
        return value


class HabitRead(BaseModel):
    id: str
    name: str
    description: str | None
    icon: str | None
    color: HabitColor
    position: int
    archived_at: datetime | None
    created_at: datetime
    schedule: ScheduleRead


class HabitList(BaseModel):
    items: list[HabitRead]
    total: int


class HabitOrder(BaseModel):
    habit_ids: list[str]
