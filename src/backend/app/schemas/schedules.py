from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

ScheduleType = Literal["daily", "weekdays", "times_per_week"]
Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

WEEKDAY_ORDER: tuple[Weekday, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class ScheduleIn(BaseModel):
    """A schedule rule; fields irrelevant to `type` are ignored (FR-002, FR-003)."""

    type: ScheduleType
    weekdays: list[Weekday] | None = None
    times_per_week: int | None = Field(default=None, ge=1, le=7)

    @model_validator(mode="after")
    def _normalize(self) -> Self:
        if self.type == "weekdays":
            if not self.weekdays:
                raise ValueError("choose at least one weekday")
            self.weekdays = sorted(set(self.weekdays), key=WEEKDAY_ORDER.index)
            self.times_per_week = None
        elif self.type == "times_per_week":
            if self.times_per_week is None:
                raise ValueError("times_per_week is required")
            self.weekdays = None
            if self.times_per_week == 7:
                self.type = "daily"
                self.times_per_week = None
        else:
            self.weekdays = None
            self.times_per_week = None
        return self


class ScheduleRead(BaseModel):
    type: ScheduleType
    weekdays: list[Weekday]
    times_per_week: int | None
    effective_from: date
