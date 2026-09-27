"""Spec 004 pure streak logic (research R1, R2; spec Clarifications)."""

import random
from datetime import date, timedelta

import pytest

from app.models import Schedule
from app.services.streaks import Streak, compute_streak
from tests.factories import build_schedule

MWF = 21  # Mon | Wed | Fri
SUNDAYS = 64
TODAY = date(2026, 9, 26)  # Saturday
MON_7 = date(2026, 9, 7)
MON_14 = date(2026, 9, 14)
MON_21 = date(2026, 9, 21)
TUE_22 = date(2026, 9, 22)
WED_23 = date(2026, 9, 23)
THU_24 = date(2026, 9, 24)
FRI_25 = date(2026, 9, 25)
SUN_27 = date(2026, 9, 27)
MUCH_LATER = date(2026, 10, 15)
ZERO = Streak(current=0, current_start=None, longest=0, longest_start=None, longest_end=None)


def _sept(*days: int) -> set[date]:
    return {date(2026, 9, day) for day in days}


def _span(first: date, last: date) -> set[date]:
    return {first + timedelta(days=offset) for offset in range((last - first).days + 1)}


def _daily(effective_from: date = date(2026, 9, 1)) -> list[Schedule]:
    return [build_schedule(effective_from)]


def _mwf(effective_from: date = MON_21) -> list[Schedule]:
    return [build_schedule(effective_from, "weekdays", weekdays=MWF)]


def _three_a_week(effective_from: date = MON_7) -> list[Schedule]:
    return [build_schedule(effective_from, "times_per_week", times_per_week=3)]


# --- US1 Current streak (FR-001, FR-004) --------------------------------------


def test_us1_s1_fr001_three_consecutive_days_including_today_is_3() -> None:
    assert compute_streak(_daily(), _sept(24, 25, 26), TODAY) == Streak(
        current=3, current_start=THU_24, longest=3, longest_start=THU_24, longest_end=TODAY
    )


def test_us1_s2_fr001_yesterday_still_counts_before_today_ends() -> None:
    assert compute_streak(_daily(), _sept(24, 25), TODAY) == Streak(
        current=2, current_start=THU_24, longest=2, longest_start=THU_24, longest_end=FRI_25
    )


def test_us1_s3_fr001_gap_two_days_ago_counts_only_days_after_gap() -> None:
    completed = _sept(20, 21, 22, 23, 25, 26)
    assert compute_streak(_daily(), completed, TODAY) == Streak(
        current=2,
        current_start=FRI_25,
        longest=4,
        longest_start=date(2026, 9, 20),
        longest_end=WED_23,
    )


def test_fr001_missed_yesterday_breaks_run_while_today_is_pending() -> None:
    assert compute_streak(_daily(), _sept(23, 24), TODAY) == Streak(
        current=0, current_start=None, longest=2, longest_start=WED_23, longest_end=THU_24
    )


def test_fr001_completed_today_after_missed_yesterday_is_1() -> None:
    assert compute_streak(_daily(), _sept(23, 24, 26), TODAY) == Streak(
        current=1, current_start=TODAY, longest=2, longest_start=WED_23, longest_end=THU_24
    )


def test_edge_fr001_habit_created_today_with_one_check_in_is_1() -> None:
    assert compute_streak(_daily(TODAY), {TODAY}, TODAY) == Streak(
        current=1, current_start=TODAY, longest=1, longest_start=TODAY, longest_end=TODAY
    )


def test_edge_fr001_habit_created_today_without_check_in_is_0() -> None:
    assert compute_streak(_daily(TODAY), set(), TODAY) == ZERO


def test_fr001_no_check_ins_is_zero_without_dates() -> None:
    assert compute_streak(_daily(), set(), TODAY) == ZERO


def test_edge_fr004_undo_today_recalculates_from_remaining_check_ins() -> None:
    before = compute_streak(_daily(), _sept(24, 25, 26), TODAY)
    after = compute_streak(_daily(), _sept(24, 25), TODAY)
    assert (before.current, after.current) == (3, 2)
    assert after.longest_end == FRI_25


def test_r1_fr001_backfilled_check_ins_before_first_schedule_are_counted() -> None:
    assert compute_streak(_daily(TODAY), _sept(24, 25, 26), TODAY) == Streak(
        current=3, current_start=THU_24, longest=3, longest_start=THU_24, longest_end=TODAY
    )


def test_r1_fr003_backfill_before_first_schedule_follows_first_schedule_rule() -> None:
    # MWF created Wednesday: Monday is backfilled; Tuesday is unscheduled under MWF.
    assert compute_streak(_mwf(WED_23), _sept(21, 22, 23), THU_24) == Streak(
        current=2, current_start=MON_21, longest=2, longest_start=MON_21, longest_end=WED_23
    )


# --- US2 Longest streak (FR-002) ----------------------------------------------


def test_us2_s1_fr002_runs_of_5_and_2_give_longest_5_with_its_dates() -> None:
    completed = _sept(15, 16, 17, 18, 19, 25, 26)
    assert compute_streak(_daily(), completed, TODAY) == Streak(
        current=2,
        current_start=FRI_25,
        longest=5,
        longest_start=date(2026, 9, 15),
        longest_end=date(2026, 9, 19),
    )


def test_fr002_longest_tie_with_current_keeps_earliest_run() -> None:
    assert compute_streak(_daily(), _sept(21, 22, 25, 26), TODAY) == Streak(
        current=2, current_start=FRI_25, longest=2, longest_start=MON_21, longest_end=TUE_22
    )


def test_fr002_longest_tie_between_past_runs_keeps_earliest_run() -> None:
    completed = _sept(17, 18, 20, 21, 23, 24)
    assert compute_streak(_daily(), completed, TODAY) == Streak(
        current=0,
        current_start=None,
        longest=2,
        longest_start=date(2026, 9, 17),
        longest_end=date(2026, 9, 18),
    )


def test_fr002_current_run_is_longest_when_it_exceeds_past_runs() -> None:
    completed = _sept(10, 11) | _span(date(2026, 9, 20), TODAY)
    assert compute_streak(_daily(), completed, TODAY) == Streak(
        current=7,
        current_start=date(2026, 9, 20),
        longest=7,
        longest_start=date(2026, 9, 20),
        longest_end=TODAY,
    )


def _rows(kind: str, start: date) -> list[Schedule]:
    if kind == "daily":
        return _daily(start)
    if kind == "mwf":
        return _mwf(start)
    if kind == "three-a-week":
        return _three_a_week(start)
    return [
        build_schedule(start, "weekdays", weekdays=MWF),
        build_schedule(start + timedelta(days=21)),
        build_schedule(start + timedelta(days=42), "times_per_week", times_per_week=2),
    ]


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("kind", ["daily", "mwf", "three-a-week", "history"])
def test_fr002_streak_invariants_hold_for_random_histories(kind: str, seed: int) -> None:
    rng = random.Random(seed)
    start = date(2026, 7, 13)  # a Monday
    today = start + timedelta(days=69)
    completed = {start + timedelta(days=n) for n in range(70) if rng.random() < 0.7}
    streak = compute_streak(_rows(kind, start), completed, today)
    assert streak.longest >= streak.current >= 0
    assert (streak.current == 0) is (streak.current_start is None)
    assert (streak.longest == 0) is (streak.longest_start is None)
    assert (streak.longest == 0) is (streak.longest_end is None)
    if streak.current_start is not None:
        assert streak.current_start in completed
        assert streak.current_start <= today
    if streak.longest_start is not None and streak.longest_end is not None:
        assert {streak.longest_start, streak.longest_end} <= completed
        assert streak.longest_start <= streak.longest_end <= today


# --- US3 Specific weekdays (FR-003; Clarifications) ---------------------------


def test_us3_s1_fr003_mwf_completed_mon_and_wed_is_2_on_thursday() -> None:
    assert compute_streak(_mwf(), _sept(21, 23), THU_24) == Streak(
        current=2, current_start=MON_21, longest=2, longest_start=MON_21, longest_end=WED_23
    )


def test_us3_s2_fr003_mwf_not_completed_friday_is_0_on_saturday() -> None:
    assert compute_streak(_mwf(), _sept(21, 23), TODAY) == Streak(
        current=0, current_start=None, longest=2, longest_start=MON_21, longest_end=WED_23
    )


def test_fr001_mwf_scheduled_friday_is_pending_on_friday() -> None:
    assert compute_streak(_mwf(), _sept(21, 23), FRI_25).current == 2


def test_fr001_mwf_viewed_sunday_counts_through_friday() -> None:
    assert compute_streak(_mwf(), _sept(21, 23, 25), SUN_27) == Streak(
        current=3, current_start=MON_21, longest=3, longest_start=MON_21, longest_end=FRI_25
    )


def test_fr003_unscheduled_days_do_not_break_mwf_run_across_weeks() -> None:
    assert compute_streak(_mwf(MON_14), _sept(14, 16, 18, 21, 23), THU_24) == Streak(
        current=5, current_start=MON_14, longest=5, longest_start=MON_14, longest_end=WED_23
    )


def test_clarification_fr003_tuesday_check_in_on_mwf_is_ignored() -> None:
    assert compute_streak(_mwf(), _sept(21, 22, 23), THU_24) == Streak(
        current=2, current_start=MON_21, longest=2, longest_start=MON_21, longest_end=WED_23
    )


def test_clarification_fr003_only_unscheduled_check_ins_give_no_streak() -> None:
    assert compute_streak(_mwf(), _sept(22, 24), THU_24) == ZERO


# --- Schedule history (FR-003; spec 005 FR-006 / US4) -------------------------


def _mwf_then_daily_from_saturday() -> list[Schedule]:
    return [build_schedule(MON_21, "weekdays", weekdays=MWF), build_schedule(TODAY)]


def test_fr003_schedule_change_mwf_to_daily_keeps_run_while_saturday_pending() -> None:
    assert compute_streak(_mwf_then_daily_from_saturday(), _sept(21, 23, 25), TODAY) == Streak(
        current=3, current_start=MON_21, longest=3, longest_start=MON_21, longest_end=FRI_25
    )


def test_fr003_schedule_change_mwf_to_daily_extends_with_saturday_check_in() -> None:
    completed = _sept(21, 23, 25, 26)
    assert compute_streak(_mwf_then_daily_from_saturday(), completed, TODAY) == Streak(
        current=4, current_start=MON_21, longest=4, longest_start=MON_21, longest_end=TODAY
    )


def test_fr003_schedule_history_input_order_does_not_matter() -> None:
    rows = list(reversed(_mwf_then_daily_from_saturday()))
    assert compute_streak(rows, _sept(21, 23, 25, 26), TODAY).current == 4


def test_fr003_schedule_change_daily_to_mwf_keeps_run() -> None:
    rows = [build_schedule(MON_14), build_schedule(MON_21, "weekdays", weekdays=MWF)]
    completed = _span(MON_14, date(2026, 9, 20)) | _sept(21, 23)
    assert compute_streak(rows, completed, THU_24) == Streak(
        current=9, current_start=MON_14, longest=9, longest_start=MON_14, longest_end=WED_23
    )


def test_fr003_days_before_schedule_change_use_the_old_rule() -> None:
    rows = [build_schedule(MON_14), build_schedule(MON_21, "weekdays", weekdays=MWF)]
    completed = _sept(14, 15, 16, 18, 19, 20, 21, 23)
    assert compute_streak(rows, completed, THU_24) == Streak(
        current=5,
        current_start=date(2026, 9, 18),
        longest=5,
        longest_start=date(2026, 9, 18),
        longest_end=WED_23,
    )


# --- Times per week (FR-003; Clarifications) ----------------------------------


def test_clarification_fr003_met_weeks_chain_with_open_week() -> None:
    completed = _sept(7, 9, 11, 14, 15, 16, 22)
    assert compute_streak(_three_a_week(), completed, TODAY) == Streak(
        current=7, current_start=MON_7, longest=7, longest_start=MON_7, longest_end=TUE_22
    )


def test_clarification_fr003_open_week_without_check_ins_does_not_break() -> None:
    completed = _sept(7, 9, 11, 14, 16, 18)
    assert compute_streak(_three_a_week(), completed, WED_23) == Streak(
        current=6,
        current_start=MON_7,
        longest=6,
        longest_start=MON_7,
        longest_end=date(2026, 9, 18),
    )


def test_clarification_fr003_sunday_of_open_week_is_still_in_progress() -> None:
    completed = _sept(14, 15, 16, 21)
    assert compute_streak(_three_a_week(MON_14), completed, SUN_27) == Streak(
        current=4, current_start=MON_14, longest=4, longest_start=MON_14, longest_end=MON_21
    )


def test_clarification_fr003_unmet_past_week_breaks_the_streak() -> None:
    # The week of 7 Sep has 2 of 3 and has ended; only later weeks count.
    completed = _sept(7, 9, 14, 15, 16, 21)
    assert compute_streak(_three_a_week(), completed, TODAY) == Streak(
        current=4, current_start=MON_14, longest=4, longest_start=MON_14, longest_end=MON_21
    )


def test_clarification_fr003_empty_past_week_breaks_run_after_met_week() -> None:
    completed = _sept(7, 9, 11, 21, 22, 23)
    assert compute_streak(_three_a_week(), completed, TODAY) == Streak(
        current=3,
        current_start=MON_21,
        longest=3,
        longest_start=MON_7,
        longest_end=date(2026, 9, 11),
    )


def test_clarification_fr003_check_ins_beyond_target_are_ignored() -> None:
    assert compute_streak(_three_a_week(MON_21), _sept(21, 22, 23, 24), TODAY) == Streak(
        current=3, current_start=MON_21, longest=3, longest_start=MON_21, longest_end=WED_23
    )


def test_clarification_fr003_extras_do_not_carry_into_next_week() -> None:
    completed = _sept(14, 15, 16, 17, 21)
    assert compute_streak(_three_a_week(MON_14), completed, TODAY) == Streak(
        current=4, current_start=MON_14, longest=4, longest_start=MON_14, longest_end=MON_21
    )


def test_r5_fr003_times_per_week_weeks_start_on_monday() -> None:
    # Sat 19 + Sun 20 are 2 of 3 in the ended week of 14 Sep; Mon 21 opens a new week.
    streak = compute_streak(_three_a_week(MON_14), _sept(19, 20, 21), TODAY)
    assert (streak.current, streak.current_start) == (1, MON_21)


def test_fr003_times_per_week_week_spanning_new_year() -> None:
    start = date(2026, 12, 21)
    completed = {
        start,
        date(2026, 12, 22),
        date(2026, 12, 23),
        date(2026, 12, 29),
        date(2026, 12, 31),
        date(2027, 1, 2),
        date(2027, 1, 4),
    }
    assert compute_streak(_three_a_week(start), completed, date(2027, 1, 5)) == Streak(
        current=7,
        current_start=start,
        longest=7,
        longest_start=start,
        longest_end=date(2027, 1, 4),
    )


def test_clarification_fr003_times_per_week_created_today_without_check_ins_is_0() -> None:
    assert compute_streak(_three_a_week(TODAY), set(), TODAY) == ZERO


# --- Archived habits freeze (edge case; research R2) --------------------------


def test_edge_r2_archived_habit_keeps_streak_at_archive_date() -> None:
    archived_on = date(2026, 9, 20)
    completed = _sept(18, 19, 20)
    assert compute_streak(_daily(), completed, MUCH_LATER, frozen_at=archived_on) == Streak(
        current=3,
        current_start=date(2026, 9, 18),
        longest=3,
        longest_start=date(2026, 9, 18),
        longest_end=archived_on,
    )


def test_edge_r2_archive_date_itself_is_pending() -> None:
    streak = compute_streak(_daily(), _sept(18, 19), MUCH_LATER, frozen_at=date(2026, 9, 20))
    assert (streak.current, streak.current_start) == (2, date(2026, 9, 18))


def test_edge_r2_same_history_without_freeze_is_broken_by_later_days() -> None:
    assert compute_streak(_daily(), _sept(18, 19, 20), MUCH_LATER) == Streak(
        current=0,
        current_start=None,
        longest=3,
        longest_start=date(2026, 9, 18),
        longest_end=date(2026, 9, 20),
    )


def test_edge_r2_archived_times_per_week_open_week_does_not_break() -> None:
    completed = _sept(14, 15, 16, 21)
    streak = compute_streak(_three_a_week(MON_14), completed, MUCH_LATER, frozen_at=WED_23)
    assert (streak.current, streak.current_start) == (4, MON_14)


# --- Calendar and DST boundaries (SC-002) -------------------------------------


@pytest.mark.parametrize(
    ("first", "last"),
    [
        (date(2026, 3, 27), date(2026, 3, 31)),
        (date(2026, 10, 23), date(2026, 10, 27)),
        (date(2026, 9, 29), date(2026, 10, 2)),
        (date(2026, 12, 30), date(2027, 1, 2)),
        (date(2028, 2, 27), date(2028, 3, 1)),
    ],
    ids=[
        "europe-madrid-spring-forward",
        "europe-madrid-fall-back",
        "month-boundary",
        "year-boundary",
        "leap-day",
    ],
)
def test_sc002_fr001_daily_run_across_boundary_counts_each_day_once(
    first: date, last: date
) -> None:
    length = (last - first).days + 1
    assert compute_streak(_daily(first), _span(first, last), last) == Streak(
        current=length,
        current_start=first,
        longest=length,
        longest_start=first,
        longest_end=last,
    )


def test_sc002_fr001_missed_dst_spring_forward_day_breaks_daily_run() -> None:
    completed = {date(2026, 3, 28), date(2026, 3, 30)}
    assert compute_streak(_daily(date(2026, 3, 28)), completed, date(2026, 3, 30)) == Streak(
        current=1,
        current_start=date(2026, 3, 30),
        longest=1,
        longest_start=date(2026, 3, 28),
        longest_end=date(2026, 3, 28),
    )


def test_sc002_fr003_sunday_habit_across_dst_spring_forward() -> None:
    rows = [build_schedule(date(2026, 3, 22), "weekdays", weekdays=SUNDAYS)]
    completed = {date(2026, 3, 22), date(2026, 3, 29), date(2026, 4, 5)}
    assert compute_streak(rows, completed, date(2026, 4, 6)) == Streak(
        current=3,
        current_start=date(2026, 3, 22),
        longest=3,
        longest_start=date(2026, 3, 22),
        longest_end=date(2026, 4, 5),
    )
