from datetime import date

from pydantic import BaseModel


class StreakRead(BaseModel):
    current: int
    current_start: date | None
    longest: int
    longest_start: date | None
    longest_end: date | None
