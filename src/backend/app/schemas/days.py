from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.habits import HabitRead


class WeekProgress(BaseModel):
    completed: int
    target: int


class DayHabit(BaseModel):
    habit: HabitRead
    status: Literal["due", "done_for_week"]
    completed: bool
    note: str | None
    week: WeekProgress | None


class DaySummary(BaseModel):
    date: date
    items: list[DayHabit]
    due_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    habit_count: int = Field(ge=0)
