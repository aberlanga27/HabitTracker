from datetime import date

from sqlmodel import Field, SQLModel, UniqueConstraint

from app.core.ids import new_id


class Schedule(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("habit_id", "effective_from", name="uq_schedule_habit_effective_from"),
    )

    id: str = Field(default_factory=new_id, primary_key=True)
    habit_id: str = Field(foreign_key="habit.id", index=True, ondelete="CASCADE")
    type: str = Field(default="daily", max_length=16)
    weekdays: int = 0
    times_per_week: int | None = None
    effective_from: date
