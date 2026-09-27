"""Day summary: which habits are due on a local date and their completion (spec 005 FR-004)."""

from collections import defaultdict
from datetime import date, timedelta

from sqlmodel import Session, col, select

from app.models import CheckIn
from app.schemas.days import DayHabit, DaySummary, WeekProgress
from app.services import habits as habit_service
from app.services import schedules as schedule_service


def day_summary(session: Session, user_id: str, day: date, *, today: date) -> DaySummary:
    """Active habits due or done-for-the-week on `day`, ordered by position."""
    habits = habit_service.active_habits(session, user_id)
    habit_ids = [habit.id for habit in habits]
    schedules = schedule_service.load_schedules(session, habit_ids)
    start = schedule_service.week_start(day)
    week_rows = session.exec(
        select(CheckIn).where(
            col(CheckIn.habit_id).in_(habit_ids),
            col(CheckIn.local_date) >= start,
            col(CheckIn.local_date) <= start + timedelta(days=6),
        )
    ).all()
    week: dict[str, list[CheckIn]] = defaultdict(list)
    for row in week_rows:
        week[row.habit_id].append(row)

    items: list[DayHabit] = []
    for habit in habits:
        rule = schedule_service.rule_of(schedule_service.schedule_on(schedules[habit.id], day))
        rows = week[habit.id]
        before = sum(1 for row in rows if row.local_date < day)
        due = schedule_service.is_due(rule, day, before)
        if not due and rule.type != schedule_service.TIMES_PER_WEEK:
            continue
        on_day = next((row for row in rows if row.local_date == day), None)
        progress = None
        if rule.type == schedule_service.TIMES_PER_WEEK and rule.times_per_week is not None:
            through = sum(1 for row in rows if row.local_date <= day)
            progress = WeekProgress(completed=through, target=rule.times_per_week)
        items.append(
            DayHabit(
                habit=habit_service.to_read(habit, schedules[habit.id], today),
                status="due" if due else "done_for_week",
                completed=on_day is not None,
                note=on_day.note if on_day else None,
                week=progress,
            )
        )
    return DaySummary(date=day, items=items)
