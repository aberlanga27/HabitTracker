"""Day summary: due habits, completion, and progress counts (spec 005 FR-004, spec 006)."""

from datetime import date, timedelta

from sqlmodel import Session, col, select

from app.core.auth import Viewer
from app.models import CheckIn
from app.schemas.days import DayHabit, DaySummary, WeekProgress
from app.services import habits as habit_service
from app.services import schedules as schedule_service


def day_summary(session: Session, viewer: Viewer, day: date) -> DaySummary:
    """Active habits due or done-for-the-week on `day`, ordered by position."""
    habits = habit_service.active_habits(session, viewer.user_id)
    habit_ids = [habit.id for habit in habits]
    schedules = schedule_service.load_schedules(session, habit_ids)
    completed = habit_service.completed_dates(session, habit_ids)
    notes = dict(
        session.exec(
            select(CheckIn.habit_id, CheckIn.note).where(
                col(CheckIn.habit_id).in_(habit_ids), CheckIn.local_date == day
            )
        ).all()
    )
    start = schedule_service.week_start(day)
    end = start + timedelta(days=6)

    items: list[DayHabit] = []
    for habit in habits:
        rule = schedule_service.rule_of(schedule_service.schedule_on(schedules[habit.id], day))
        week = sorted(d for d in completed[habit.id] if start <= d <= end)
        before = sum(1 for d in week if d < day)
        due = schedule_service.is_due(rule, day, before)
        if not due and rule.type != schedule_service.TIMES_PER_WEEK:
            continue
        progress = None
        if rule.type == schedule_service.TIMES_PER_WEEK and rule.times_per_week is not None:
            through = sum(1 for d in week if d <= day)
            progress = WeekProgress(completed=through, target=rule.times_per_week)
        items.append(
            DayHabit(
                habit=habit_service.to_read(
                    habit, schedules[habit.id], completed[habit.id], viewer
                ),
                status="due" if due else "done_for_week",
                completed=day in completed[habit.id],
                note=notes.get(habit.id),
                week=progress,
            )
        )
    due_items = [item for item in items if item.status == "due"]
    return DaySummary(
        date=day,
        items=items,
        due_count=len(due_items),
        completed_count=sum(1 for item in due_items if item.completed),
        habit_count=len(habits),
    )
