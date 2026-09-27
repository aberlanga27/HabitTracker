"""Spec 004 SC-001: a streak over 2 years of daily check-ins completes in under 20 ms."""

import time
from datetime import date, timedelta

import pytest

from app.services.streaks import compute_streak
from tests.factories import build_schedule

DAYS = 730
RUNS = 20
BUDGET_SECONDS = 0.020
TODAY = date(2026, 9, 26)


@pytest.mark.perf
def test_sc001_perf_streak_two_years_of_daily_check_ins_under_20ms() -> None:
    first = TODAY - timedelta(days=DAYS - 1)
    schedules = [build_schedule(first)]
    completed = {first + timedelta(days=offset) for offset in range(DAYS)}
    started = time.perf_counter()
    streaks = [compute_streak(schedules, completed, TODAY) for _ in range(RUNS)]
    average = (time.perf_counter() - started) / RUNS
    assert {(streak.current, streak.longest) for streak in streaks} == {(DAYS, DAYS)}
    assert average < BUDGET_SECONDS, f"average {average * 1000:.3f} ms per 2-year streak"
