"""Spec 005 SC-001: "is due today" for 50 habits completes in under 10 ms."""

import time
from datetime import date, timedelta

import pytest

from app.models import Schedule
from app.services.schedules import is_due, rule_of, schedule_on

HABITS = 50
RUNS = 1000
BUDGET_SECONDS = 0.010
TODAY = date(2026, 9, 26)


def _schedules(habit: int) -> list[Schedule]:
    start = date(2026, 1, 5) + timedelta(days=habit)
    return [
        Schedule(
            habit_id=f"h{habit}",
            type="daily",
            weekdays=0,
            times_per_week=None,
            effective_from=start,
        ),
        Schedule(
            habit_id=f"h{habit}",
            type="weekdays",
            weekdays=21,
            times_per_week=None,
            effective_from=start + timedelta(days=60),
        ),
        Schedule(
            habit_id=f"h{habit}",
            type="times_per_week",
            weekdays=0,
            times_per_week=1 + habit % 6,
            effective_from=start + timedelta(days=120),
        ),
    ]


@pytest.mark.perf
def test_sc001_is_due_for_50_habits_under_10ms() -> None:
    habits = [list(reversed(_schedules(habit))) for habit in range(HABITS)]
    started = time.perf_counter()
    for _ in range(RUNS):
        due = [is_due(rule_of(schedule_on(rows, TODAY)), TODAY, 2) for rows in habits]
    average = (time.perf_counter() - started) / RUNS
    assert len(due) == HABITS
    assert average < BUDGET_SECONDS, f"average {average * 1000:.3f} ms per 50-habit evaluation"
