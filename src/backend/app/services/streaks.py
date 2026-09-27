"""Schedule-aware streaks computed on read (spec 004). Pure: takes local dates only."""

from collections.abc import Sequence, Set
from dataclasses import dataclass
from datetime import date, timedelta

from app.models import Schedule
from app.services import schedules as schedule_service


@dataclass(frozen=True)
class Streak:
    current: int
    current_start: date | None
    longest: int
    longest_start: date | None
    longest_end: date | None


def compute_streak(
    schedules: Sequence[Schedule],
    completed: Set[date],
    today: date,
    frozen_at: date | None = None,
) -> Streak:
    """Current and longest runs of completed scheduled days (FR-001..FR-003).

    The end date (today, or `frozen_at` for archived habits) is still in progress, so missing it
    never breaks a run. Times-per-week habits break only when a finished week missed its target.
    """
    end = frozen_at or today
    ordered = sorted(schedules, key=lambda s: s.effective_from)
    start = min([ordered[0].effective_from, *completed])

    run = 0
    run_start: date | None = None
    longest, longest_start, longest_end = 0, None, None
    week_done = 0

    day = start
    while day <= end:
        if day.weekday() == 0:
            week_done = 0
        rule = schedule_service.rule_of(schedule_service.schedule_on(ordered, day))
        done = day in completed
        if rule.type == schedule_service.TIMES_PER_WEEK and rule.times_per_week is not None:
            if done and week_done < rule.times_per_week:
                run, run_start = run + 1, run_start or day
                week_done += 1
            elif done:
                week_done += 1
            week_over = day.weekday() == 6 and day < end
            if week_over and week_done < rule.times_per_week:
                run, run_start = 0, None
        elif schedule_service.is_due(rule, day, 0):
            if done:
                run, run_start = run + 1, run_start or day
            elif day < end:
                run, run_start = 0, None
        if done and run > longest:
            longest, longest_start, longest_end = run, run_start, day
        day += timedelta(days=1)

    return Streak(
        current=run,
        current_start=run_start if run else None,
        longest=longest,
        longest_start=longest_start,
        longest_end=longest_end,
    )
