"""Habit CRUD, archive/restore, and ordering (spec 002). Every query is scoped to the owner."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Habit
from app.schemas.habits import HabitCreate, HabitUpdate

MAX_ACTIVE_HABITS = 50

logger = get_logger("habits")


class HabitLimitReachedError(ConflictError):
    code = "HABIT_LIMIT_REACHED"


def _active_count(session: Session, user_id: str) -> int:
    return session.exec(
        select(func.count())
        .select_from(Habit)
        .where(Habit.user_id == user_id, col(Habit.archived_at).is_(None))
    ).one()


def _ensure_capacity(session: Session, user_id: str) -> None:
    if _active_count(session, user_id) >= MAX_ACTIVE_HABITS:
        raise HabitLimitReachedError(
            f"Habit limit reached ({MAX_ACTIVE_HABITS})", details={"limit": MAX_ACTIVE_HABITS}
        )


def _next_position(session: Session, user_id: str) -> int:
    current = session.exec(
        select(func.max(Habit.position)).where(
            Habit.user_id == user_id, col(Habit.archived_at).is_(None)
        )
    ).one()
    return 0 if current is None else current + 1


def list_habits(session: Session, user_id: str, *, archived: bool) -> Sequence[Habit]:
    archived_filter = (
        col(Habit.archived_at).is_not(None) if archived else col(Habit.archived_at).is_(None)
    )
    return session.exec(
        select(Habit)
        .where(Habit.user_id == user_id, archived_filter)
        .order_by(col(Habit.position), col(Habit.created_at))
    ).all()


def get_owned(session: Session, user_id: str, habit_id: str) -> Habit:
    """Return the user's habit or raise NotFoundError (also for other users' habits)."""
    habit = session.exec(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    ).first()
    if habit is None:
        raise NotFoundError("Habit not found")
    return habit


def create(session: Session, user_id: str, data: HabitCreate, *, now: datetime) -> Habit:
    """Create a habit at the end of the list. Raises HabitLimitReachedError (FR-006)."""
    _ensure_capacity(session, user_id)
    habit = Habit(
        user_id=user_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color,
        position=_next_position(session, user_id),
        created_at=now,
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    logger.info("habit created", extra={"habit_id": habit.id})
    return habit


def update(session: Session, user_id: str, habit_id: str, data: HabitUpdate) -> Habit:
    habit = get_owned(session, user_id, habit_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def archive(session: Session, user_id: str, habit_id: str, *, now: datetime) -> Habit:
    habit = get_owned(session, user_id, habit_id)
    if habit.archived_at is None:
        habit.archived_at = now
        session.add(habit)
        session.commit()
        session.refresh(habit)
        logger.info("habit archived", extra={"habit_id": habit.id})
    return habit


def restore(session: Session, user_id: str, habit_id: str) -> Habit:
    """Reactivate an archived habit at the end of the list. Raises HabitLimitReachedError."""
    habit = get_owned(session, user_id, habit_id)
    if habit.archived_at is not None:
        _ensure_capacity(session, user_id)
        habit.position = _next_position(session, user_id)
        habit.archived_at = None
        session.add(habit)
        session.commit()
        session.refresh(habit)
        logger.info("habit restored", extra={"habit_id": habit.id})
    return habit


def delete(session: Session, user_id: str, habit_id: str) -> None:
    habit = get_owned(session, user_id, habit_id)
    session.delete(habit)
    session.commit()
    logger.info("habit deleted", extra={"habit_id": habit_id})


def reorder(session: Session, user_id: str, habit_ids: list[str]) -> Sequence[Habit]:
    """Rewrite positions to match `habit_ids`, which must be exactly the active habits."""
    active = {habit.id: habit for habit in list_habits(session, user_id, archived=False)}
    if len(habit_ids) != len(set(habit_ids)) or set(habit_ids) != set(active):
        raise ValidationError(
            "habit_ids must list every active habit exactly once",
            details={"fields": [{"loc": ["body", "habit_ids"], "msg": "mismatch"}]},
        )
    for position, habit_id in enumerate(habit_ids):
        active[habit_id].position = position
        session.add(active[habit_id])
    session.commit()
    return list_habits(session, user_id, archived=False)
