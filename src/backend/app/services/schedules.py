"""Schedule rules and "is due" evaluation (spec 005). Pure functions take local dates."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlmodel import Session, col, select

from app.models import Schedule

WEEKDAY_NAMES: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAILY = "daily"
WEEKDAYS = "weekdays"
TIMES_PER_WEEK = "times_per_week"


@dataclass(frozen=True)
class Rule:
    type: str
    weekdays: frozenset[int] = field(default_factory=frozenset)
    times_per_week: int | None = None


def weekdays_to_mask(days: Iterable[int]) -> int:
    mask = 0
    for day in days:
        mask |= 1 << day
    return mask


def mask_to_weekdays(mask: int) -> frozenset[int]:
    return frozenset(day for day in range(7) if mask & (1 << day))


def week_start(day: date) -> date:
    """Monday of `day`'s week. TODO(spec-012): honor the user's configured week start."""
    return day - timedelta(days=day.weekday())


def is_due(rule: Rule, day: date, completed_before_in_week: int) -> bool:
    """Whether a habit with `rule` is due on local date `day` (FR-004)."""
    if rule.type == WEEKDAYS:
        return day.weekday() in rule.weekdays
    if rule.type == TIMES_PER_WEEK and rule.times_per_week is not None:
        return completed_before_in_week < rule.times_per_week
    return True


def schedule_on(schedules: Sequence[Schedule], day: date) -> Schedule:
    """The schedule active on `day`; dates before the first row use the first row (FR-006)."""
    ordered = sorted(schedules, key=lambda s: s.effective_from)
    active = ordered[0]
    for schedule in ordered:
        if schedule.effective_from <= day:
            active = schedule
    return active


def rule_of(schedule: Schedule) -> Rule:
    return Rule(
        type=schedule.type,
        weekdays=mask_to_weekdays(schedule.weekdays),
        times_per_week=schedule.times_per_week,
    )


def load_schedules(session: Session, habit_ids: Sequence[str]) -> dict[str, list[Schedule]]:
    """All schedule rows for the given habits in one query, grouped by habit id."""
    grouped: dict[str, list[Schedule]] = {habit_id: [] for habit_id in habit_ids}
    if not habit_ids:
        return grouped
    rows = session.exec(
        select(Schedule)
        .where(col(Schedule.habit_id).in_(habit_ids))
        .order_by(col(Schedule.effective_from))
    ).all()
    for row in rows:
        grouped[row.habit_id].append(row)
    return grouped


def set_schedule(session: Session, habit_id: str, rule: Rule, today: date) -> None:
    """Make `rule` effective from `today` without touching history or check-ins (FR-005)."""
    rows = load_schedules(session, [habit_id])[habit_id]
    current = schedule_on(rows, today) if rows else None
    if current is not None and rule_of(current) == rule:
        return
    latest = rows[-1] if rows else None
    target = latest if latest is not None and latest.effective_from == today else None
    if target is None:
        target = Schedule(habit_id=habit_id, effective_from=today)
    target.type = rule.type
    target.weekdays = weekdays_to_mask(rule.weekdays)
    target.times_per_week = rule.times_per_week
    session.add(target)
