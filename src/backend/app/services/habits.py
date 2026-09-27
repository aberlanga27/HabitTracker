"""Habit CRUD, archive/restore, and ordering (spec 002). Every query is scoped to the owner."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Habit, Schedule
from app.schemas.habits import HabitCreate, HabitRead, HabitUpdate
from app.schemas.schedules import WEEKDAY_ORDER, ScheduleIn, ScheduleRead
from app.services import schedules as schedule_service

MAX_ACTIVE_HABITS = 50

logger = get_logger("habits")


class HabitLimitReachedError(ConflictError):
    code = "HABIT_LIMIT_REACHED"


def rule_from(data: ScheduleIn) -> schedule_service.Rule:
    return schedule_service.Rule(
        type=data.type,
        weekdays=frozenset(WEEKDAY_ORDER.index(day) for day in data.weekdays or []),
        times_per_week=data.times_per_week,
    )


def schedule_read(schedule: Schedule) -> ScheduleRead:
    rule = schedule_service.rule_of(schedule)
    return ScheduleRead.model_validate(
        {
            "type": schedule.type,
            "weekdays": [WEEKDAY_ORDER[day] for day in sorted(rule.weekdays)],
            "times_per_week": schedule.times_per_week,
            "effective_from": schedule.effective_from,
        }
    )


def to_read(habit: Habit, schedules: Sequence[Schedule], today: date) -> HabitRead:
    """Map a habit and its schedule history to `HabitRead` with the schedule active today."""
    return HabitRead.model_validate(
        {
            **habit.model_dump(exclude={"user_id"}),
            "schedule": schedule_read(schedule_service.schedule_on(schedules, today)),
        }
    )


def read_many(session: Session, habits: Sequence[Habit], today: date) -> list[HabitRead]:
    grouped = schedule_service.load_schedules(session, [habit.id for habit in habits])
    return [to_read(habit, grouped[habit.id], today) for habit in habits]


def _read_one(session: Session, habit: Habit, today: date) -> HabitRead:
    return read_many(session, [habit], today)[0]


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


def _query_habits(session: Session, user_id: str, *, archived: bool) -> Sequence[Habit]:
    archived_filter = (
        col(Habit.archived_at).is_not(None) if archived else col(Habit.archived_at).is_(None)
    )
    return session.exec(
        select(Habit)
        .where(Habit.user_id == user_id, archived_filter)
        .order_by(col(Habit.position), col(Habit.created_at))
    ).all()


def active_habits(session: Session, user_id: str) -> Sequence[Habit]:
    return _query_habits(session, user_id, archived=False)


def list_habits(session: Session, user_id: str, *, archived: bool, today: date) -> list[HabitRead]:
    return read_many(session, _query_habits(session, user_id, archived=archived), today)


def get_owned(session: Session, user_id: str, habit_id: str) -> Habit:
    """Return the user's habit or raise NotFoundError (also for other users' habits)."""
    habit = session.exec(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    ).first()
    if habit is None:
        raise NotFoundError("Habit not found")
    return habit


def get(session: Session, user_id: str, habit_id: str, *, today: date) -> HabitRead:
    return _read_one(session, get_owned(session, user_id, habit_id), today)


def create(
    session: Session, user_id: str, data: HabitCreate, *, now: datetime, today: date
) -> HabitRead:
    """Create a habit and its first schedule. Raises HabitLimitReachedError (FR-006)."""
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
    session.flush()
    schedule_service.set_schedule(session, habit.id, rule_from(data.schedule), today)
    session.commit()
    session.refresh(habit)
    logger.info("habit created", extra={"habit_id": habit.id})
    return _read_one(session, habit, today)


def update(
    session: Session, user_id: str, habit_id: str, data: HabitUpdate, *, today: date
) -> HabitRead:
    """Apply a partial update; a new schedule takes effect today (spec 005 FR-005)."""
    habit = get_owned(session, user_id, habit_id)
    for field, value in data.model_dump(exclude_unset=True, exclude={"schedule"}).items():
        setattr(habit, field, value)
    session.add(habit)
    if data.schedule is not None:
        schedule_service.set_schedule(session, habit.id, rule_from(data.schedule), today)
    session.commit()
    session.refresh(habit)
    return _read_one(session, habit, today)


def archive(
    session: Session, user_id: str, habit_id: str, *, now: datetime, today: date
) -> HabitRead:
    habit = get_owned(session, user_id, habit_id)
    if habit.archived_at is None:
        habit.archived_at = now
        session.add(habit)
        session.commit()
        session.refresh(habit)
        logger.info("habit archived", extra={"habit_id": habit.id})
    return _read_one(session, habit, today)


def restore(session: Session, user_id: str, habit_id: str, *, today: date) -> HabitRead:
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
    return _read_one(session, habit, today)


def delete(session: Session, user_id: str, habit_id: str) -> None:
    habit = get_owned(session, user_id, habit_id)
    session.delete(habit)
    session.commit()
    logger.info("habit deleted", extra={"habit_id": habit_id})


def reorder(
    session: Session, user_id: str, habit_ids: list[str], *, today: date
) -> list[HabitRead]:
    """Rewrite positions to match `habit_ids`, which must be exactly the active habits."""
    active = {habit.id: habit for habit in active_habits(session, user_id)}
    if len(habit_ids) != len(set(habit_ids)) or set(habit_ids) != set(active):
        raise ValidationError(
            "habit_ids must list every active habit exactly once",
            details={"fields": [{"loc": ["body", "habit_ids"], "msg": "mismatch"}]},
        )
    for position, habit_id in enumerate(habit_ids):
        active[habit_id].position = position
        session.add(active[habit_id])
    session.commit()
    return list_habits(session, user_id, archived=False, today=today)
