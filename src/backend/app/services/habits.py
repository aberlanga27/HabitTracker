"""Habit CRUD, archive/restore, and ordering (spec 002). Every query is scoped to the owner."""

from collections.abc import Sequence
from dataclasses import asdict
from datetime import date, datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.auth import Viewer
from app.core.clock import local_date
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import CheckIn, Habit, Schedule
from app.schemas.habits import HabitCreate, HabitRead, HabitUpdate
from app.schemas.schedules import WEEKDAY_ORDER, ScheduleIn, ScheduleRead
from app.schemas.streaks import StreakRead
from app.services import schedules as schedule_service
from app.services.streaks import compute_streak

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


def to_read(
    habit: Habit, schedules: Sequence[Schedule], completed: set[date], viewer: Viewer
) -> HabitRead:
    """Map a habit to `HabitRead` with today's schedule and its streak (spec 004 FR-005)."""
    frozen_at = (
        local_date(habit.archived_at, viewer.timezone) if habit.archived_at is not None else None
    )
    streak = compute_streak(schedules, completed, viewer.today, frozen_at)
    return HabitRead.model_validate(
        {
            **habit.model_dump(exclude={"user_id"}),
            "schedule": schedule_read(schedule_service.schedule_on(schedules, viewer.today)),
            "streak": StreakRead.model_validate(asdict(streak)),
        }
    )


def completed_dates(session: Session, habit_ids: Sequence[str]) -> dict[str, set[date]]:
    """Every check-in date for the given habits in one query, grouped by habit id."""
    grouped: dict[str, set[date]] = {habit_id: set() for habit_id in habit_ids}
    if habit_ids:
        rows = session.exec(
            select(col(CheckIn.habit_id), col(CheckIn.local_date)).where(
                col(CheckIn.habit_id).in_(habit_ids)
            )
        ).all()
        for habit_id, day in rows:
            grouped[habit_id].add(day)
    return grouped


def read_many(session: Session, habits: Sequence[Habit], viewer: Viewer) -> list[HabitRead]:
    ids = [habit.id for habit in habits]
    schedules = schedule_service.load_schedules(session, ids)
    dates = completed_dates(session, ids)
    return [to_read(habit, schedules[habit.id], dates[habit.id], viewer) for habit in habits]


def _read_one(session: Session, habit: Habit, viewer: Viewer) -> HabitRead:
    return read_many(session, [habit], viewer)[0]


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


def list_habits(session: Session, viewer: Viewer, *, archived: bool) -> list[HabitRead]:
    return read_many(session, _query_habits(session, viewer.user_id, archived=archived), viewer)


def get_owned(session: Session, user_id: str, habit_id: str) -> Habit:
    """Return the user's habit or raise NotFoundError (also for other users' habits)."""
    habit = session.exec(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    ).first()
    if habit is None:
        raise NotFoundError("Habit not found")
    return habit


def get(session: Session, viewer: Viewer, habit_id: str) -> HabitRead:
    return _read_one(session, get_owned(session, viewer.user_id, habit_id), viewer)


def create(session: Session, viewer: Viewer, data: HabitCreate, *, now: datetime) -> HabitRead:
    """Create a habit and its first schedule. Raises HabitLimitReachedError (FR-006)."""
    _ensure_capacity(session, viewer.user_id)
    habit = Habit(
        user_id=viewer.user_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color,
        position=_next_position(session, viewer.user_id),
        created_at=now,
    )
    session.add(habit)
    session.flush()
    schedule_service.set_schedule(session, habit.id, rule_from(data.schedule), viewer.today)
    session.commit()
    session.refresh(habit)
    logger.info("habit created", extra={"habit_id": habit.id})
    return _read_one(session, habit, viewer)


def update(session: Session, viewer: Viewer, habit_id: str, data: HabitUpdate) -> HabitRead:
    """Apply a partial update; a new schedule takes effect today (spec 005 FR-005)."""
    habit = get_owned(session, viewer.user_id, habit_id)
    for field, value in data.model_dump(exclude_unset=True, exclude={"schedule"}).items():
        setattr(habit, field, value)
    session.add(habit)
    if data.schedule is not None:
        schedule_service.set_schedule(session, habit.id, rule_from(data.schedule), viewer.today)
    session.commit()
    session.refresh(habit)
    return _read_one(session, habit, viewer)


def archive(session: Session, viewer: Viewer, habit_id: str, *, now: datetime) -> HabitRead:
    habit = get_owned(session, viewer.user_id, habit_id)
    if habit.archived_at is None:
        habit.archived_at = now
        session.add(habit)
        session.commit()
        session.refresh(habit)
        logger.info("habit archived", extra={"habit_id": habit.id})
    return _read_one(session, habit, viewer)


def restore(session: Session, viewer: Viewer, habit_id: str) -> HabitRead:
    """Reactivate an archived habit at the end of the list. Raises HabitLimitReachedError."""
    habit = get_owned(session, viewer.user_id, habit_id)
    if habit.archived_at is not None:
        _ensure_capacity(session, viewer.user_id)
        habit.position = _next_position(session, viewer.user_id)
        habit.archived_at = None
        session.add(habit)
        session.commit()
        session.refresh(habit)
        logger.info("habit restored", extra={"habit_id": habit.id})
    return _read_one(session, habit, viewer)


def delete(session: Session, user_id: str, habit_id: str) -> None:
    habit = get_owned(session, user_id, habit_id)
    session.delete(habit)
    session.commit()
    logger.info("habit deleted", extra={"habit_id": habit_id})


def reorder(session: Session, viewer: Viewer, habit_ids: list[str]) -> list[HabitRead]:
    """Rewrite positions to match `habit_ids`, which must be exactly the active habits."""
    active = {habit.id: habit for habit in active_habits(session, viewer.user_id)}
    if len(habit_ids) != len(set(habit_ids)) or set(habit_ids) != set(active):
        raise ValidationError(
            "habit_ids must list every active habit exactly once",
            details={"fields": [{"loc": ["body", "habit_ids"], "msg": "mismatch"}]},
        )
    for position, habit_id in enumerate(habit_ids):
        active[habit_id].position = position
        session.add(active[habit_id])
    session.commit()
    return list_habits(session, viewer, archived=False)
