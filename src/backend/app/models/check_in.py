from datetime import date, datetime

from sqlmodel import Column, Field, SQLModel, UniqueConstraint

from app.core.db import UTCDateTime
from app.core.ids import new_id


class CheckIn(SQLModel, table=True):
    __tablename__ = "check_in"
    __table_args__ = (UniqueConstraint("habit_id", "local_date", name="uq_check_in_habit_date"),)

    id: str = Field(default_factory=new_id, primary_key=True)
    habit_id: str = Field(foreign_key="habit.id", ondelete="CASCADE")
    local_date: date
    completed_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
    note: str | None = Field(default=None, max_length=280)
