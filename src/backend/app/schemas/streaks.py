from datetime import date

from pydantic import BaseModel, Field


class StreakRead(BaseModel):
    current: int = Field(ge=0)
    current_start: date | None
    longest: int = Field(ge=0)
    longest_start: date | None
    longest_end: date | None
