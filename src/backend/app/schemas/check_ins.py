from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator

MAX_NOTE = 280


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _note(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if len(value) > MAX_NOTE:
        raise ValueError(f"must be at most {MAX_NOTE} characters")
    return value


Note = Annotated[str | None, BeforeValidator(_strip), AfterValidator(_note)]


class CheckInSet(BaseModel):
    """Desired state for one habit on one local date. Omitting `note` keeps the existing one."""

    completed: bool
    note: Note = None


class CheckInState(BaseModel):
    habit_id: str
    date: date
    completed: bool
    note: str | None
    completed_at: datetime | None


class CheckInList(BaseModel):
    items: list[CheckInState]
    total: int
