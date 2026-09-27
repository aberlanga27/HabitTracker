"""Check-in toggling within the editable window (spec 003)."""

from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, col, delete, select

from app.core.clock import local_date
from app.core.errors import ConflictError, ValidationError
from app.core.ids import new_id
from app.models import CheckIn, Habit, User
from app.schemas.check_ins import CheckInSet, CheckInState
from app.services.habits import get_owned

BACKFILL_DAYS = 30


class HabitArchivedError(ConflictError):
    code = "HABIT_ARCHIVED"


class DateOutOfRangeError(ValidationError):
    code = "DATE_OUT_OF_RANGE"


def editable_window(today: date) -> tuple[date, date]:
    """Earliest and latest local dates that accept check-ins (FR-002, FR-003)."""
    return today - timedelta(days=BACKFILL_DAYS), today


def is_editable(day: date, today: date) -> bool:
    earliest, latest = editable_window(today)
    return earliest <= day <= latest


def _state(habit_id: str, day: date, row: CheckIn | None) -> CheckInState:
    return CheckInState(
        habit_id=habit_id,
        date=day,
        completed=row is not None,
        note=row.note if row else None,
        completed_at=row.completed_at if row else None,
    )


def set_check_in(
    session: Session, user: User, habit_id: str, day: date, data: CheckInSet, *, now: datetime
) -> CheckInState:
    """Idempotently set completion for `day` (FR-001, FR-004, FR-005).

    Raises NotFoundError, HabitArchivedError, or DateOutOfRangeError.
    """
    habit = get_owned(session, user.id, habit_id)
    if habit.archived_at is not None:
        raise HabitArchivedError("Archived habits cannot be checked in")
    today = local_date(now, user.timezone)
    if not is_editable(day, today):
        earliest, latest = editable_window(today)
        raise DateOutOfRangeError(
            f"Check-ins are allowed from {earliest.isoformat()} to {latest.isoformat()}",
            details={"earliest": earliest.isoformat(), "latest": latest.isoformat()},
        )

    match = (col(CheckIn.habit_id) == habit_id) & (col(CheckIn.local_date) == day)
    if not data.completed:
        session.exec(delete(CheckIn).where(match))
        session.commit()
        return _state(habit_id, day, None)

    statement = (
        insert(CheckIn)
        .values(
            id=new_id(),
            habit_id=habit_id,
            local_date=day,
            completed_at=now,
            note=data.note,
        )
        .on_conflict_do_nothing(index_elements=["habit_id", "local_date"])
    )
    session.exec(statement)
    row = session.exec(select(CheckIn).where(match)).one()
    if "note" in data.model_fields_set and row.note != data.note:
        row.note = data.note
        session.add(row)
    session.commit()
    session.refresh(row)
    return _state(habit_id, day, row)


def list_for_date(session: Session, user_id: str, day: date) -> Sequence[CheckInState]:
    rows = session.exec(
        select(CheckIn)
        .join(Habit, col(Habit.id) == col(CheckIn.habit_id))
        .where(Habit.user_id == user_id, CheckIn.local_date == day)
        .order_by(col(Habit.position))
    ).all()
    return [_state(row.habit_id, day, row) for row in rows]
