"""Spec 005 pure schedule logic (research R1, R3, R5): masks, weeks, selection, due-ness."""

import random
from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from app.models import Schedule
from app.services.schedules import (
    WEEKDAY_NAMES,
    Rule,
    is_due,
    mask_to_weekdays,
    rule_of,
    schedule_on,
    week_start,
    weekdays_to_mask,
)

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
WEEK = [date(2026, 9, 21) + timedelta(days=offset) for offset in range(7)]
WEEK_IDS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MWF = Rule(type="weekdays", weekdays=frozenset({MON, WED, FRI}))


def _row(
    effective_from: date, type_: str = "daily", *, weekdays: int = 0, times: int | None = None
) -> Schedule:
    return Schedule(
        habit_id="h",
        type=type_,
        weekdays=weekdays,
        times_per_week=times,
        effective_from=effective_from,
    )


# --- Weekday names and masks (R1) ---------------------------------------------


def test_r1_weekday_names_are_monday_first() -> None:
    assert WEEKDAY_NAMES == ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@pytest.mark.parametrize(
    ("days", "mask"),
    [
        ([MON], 1),
        ([TUE], 2),
        ([SUN], 64),
        ([MON, WED, FRI], 21),
        ([SAT, SUN], 96),
        (list(range(7)), 127),
        ([], 0),
    ],
    ids=["mon", "tue", "sun", "mon-wed-fri", "weekend", "all", "none"],
)
def test_r1_weekdays_to_mask_sets_monday_as_bit_0(days: list[int], mask: int) -> None:
    assert weekdays_to_mask(days) == mask


def test_fr002_duplicate_weekdays_collapse_in_mask() -> None:
    assert weekdays_to_mask([MON, MON, WED, WED]) == 5


@pytest.mark.parametrize(
    "days",
    [frozenset({MON}), frozenset({SUN}), frozenset({MON, WED, FRI}), frozenset(range(7))],
    ids=["mon", "sun", "mon-wed-fri", "all"],
)
def test_r1_mask_round_trips(days: frozenset[int]) -> None:
    assert mask_to_weekdays(weekdays_to_mask(days)) == days


def test_r1_mask_to_weekdays_decodes_bits() -> None:
    assert mask_to_weekdays(21) == frozenset({MON, WED, FRI})
    assert mask_to_weekdays(0) == frozenset()


def test_r1_weekdays_to_mask_accepts_any_iterable() -> None:
    assert weekdays_to_mask(iter((TUE, THU))) == 10


# --- Week boundaries (R5: Monday week start) ----------------------------------


@pytest.mark.parametrize(
    ("day", "monday"),
    [
        (date(2026, 9, 21), date(2026, 9, 21)),
        (date(2026, 9, 26), date(2026, 9, 21)),
        (date(2026, 9, 27), date(2026, 9, 21)),
        (date(2026, 9, 28), date(2026, 9, 28)),
        (date(2026, 10, 1), date(2026, 9, 28)),
        (date(2026, 1, 1), date(2025, 12, 29)),
        (date(2027, 1, 3), date(2026, 12, 28)),
        (date(2028, 2, 29), date(2028, 2, 28)),
        (date(2026, 3, 29), date(2026, 3, 23)),
        (date(2026, 10, 25), date(2026, 10, 19)),
    ],
    ids=[
        "monday-is-its-own-start",
        "saturday",
        "sunday-belongs-to-previous-monday",
        "next-monday-starts-new-week",
        "week-spanning-month",
        "week-spanning-new-year",
        "sunday-after-new-year",
        "leap-day",
        "dst-spring-forward-sunday",
        "dst-fall-back-sunday",
    ],
)
def test_r5_week_start_is_the_monday_of_the_week(day: date, monday: date) -> None:
    assert week_start(day) == monday


def test_r5_week_start_returns_a_monday_for_every_day_of_a_year() -> None:
    days = [date(2026, 1, 1) + timedelta(days=offset) for offset in range(366)]
    for day in days:
        start = week_start(day)
        assert start.weekday() == MON
        assert timedelta(0) <= day - start < timedelta(days=7)


# --- Due-ness (FR-004, R5) ----------------------------------------------------


@pytest.mark.parametrize("day", WEEK, ids=WEEK_IDS)
def test_us1_s1_fr004_daily_is_due_every_day(day: date) -> None:
    assert is_due(Rule(type="daily"), day, 0) is True


def test_fr004_daily_stays_due_regardless_of_week_count() -> None:
    assert is_due(Rule(type="daily"), date(2026, 9, 27), 6) is True


@pytest.mark.parametrize(
    ("day", "expected"),
    list(zip(WEEK, [True, False, True, False, True, False, False], strict=True)),
    ids=WEEK_IDS,
)
def test_us2_s1_fr004_mwf_habit_due_only_on_mon_wed_fri(day: date, expected: bool) -> None:
    assert is_due(MWF, day, 0) is expected


def test_us2_s1_fr004_mwf_habit_not_due_on_tuesday() -> None:
    assert is_due(MWF, date(2026, 9, 22), 0) is False


def test_fr004_weekdays_due_on_dst_spring_forward_sunday() -> None:
    sundays = Rule(type="weekdays", weekdays=frozenset({SUN}))
    assert is_due(sundays, date(2026, 3, 29), 0) is True
    assert is_due(sundays, date(2026, 3, 30), 0) is False


@pytest.mark.parametrize("before", [0, 1, 2], ids=["none", "one", "two"])
def test_us3_s1_fr004_times_per_week_due_while_below_target(before: int) -> None:
    rule = Rule(type="times_per_week", times_per_week=3)
    assert is_due(rule, date(2026, 9, 24), before) is True


@pytest.mark.parametrize("before", [3, 4], ids=["at-target", "above-target"])
def test_us3_s2_fr004_times_per_week_not_due_once_target_reached(before: int) -> None:
    rule = Rule(type="times_per_week", times_per_week=3)
    assert is_due(rule, date(2026, 9, 24), before) is False


def test_fr003_once_per_week_not_due_after_one_check_in() -> None:
    rule = Rule(type="times_per_week", times_per_week=1)
    assert is_due(rule, date(2026, 9, 21), 0) is True
    assert is_due(rule, date(2026, 9, 22), 1) is False


@pytest.mark.parametrize("before", range(7), ids=[f"{n}-before" for n in range(7)])
def test_edge_fr003_seven_per_week_is_equivalent_to_daily(before: int) -> None:
    day = WEEK[before]
    seven = Rule(type="times_per_week", times_per_week=7)
    assert is_due(seven, day, before) is is_due(Rule(type="daily"), day, before)


# --- Schedule selection (FR-006, R3) ------------------------------------------


def test_fr006_single_schedule_applies_to_every_date() -> None:
    only = _row(date(2026, 9, 21))
    assert schedule_on([only], date(2026, 9, 21)) is only
    assert schedule_on([only], date(2027, 1, 1)) is only


def test_r3_date_before_first_schedule_uses_first_schedule() -> None:
    first = _row(date(2026, 9, 21), "weekdays", weekdays=21)
    later = _row(date(2026, 9, 24))
    assert schedule_on([first, later], date(2026, 9, 1)) is first


def test_fr006_date_uses_schedule_active_at_that_time() -> None:
    first = _row(date(2026, 9, 21), "weekdays", weekdays=21)
    second = _row(date(2026, 9, 24))
    third = _row(date(2026, 10, 5), "times_per_week", times=3)
    rows = [first, second, third]
    assert schedule_on(rows, date(2026, 9, 23)) is first
    assert schedule_on(rows, date(2026, 9, 24)) is second
    assert schedule_on(rows, date(2026, 10, 4)) is second
    assert schedule_on(rows, date(2026, 10, 5)) is third
    assert schedule_on(rows, date(2027, 1, 1)) is third


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_fr006_schedule_on_ignores_input_order(seed: int) -> None:
    rows: list[Schedule] = [
        _row(date(2026, 9, 21), "weekdays", weekdays=21),
        _row(date(2026, 9, 24)),
        _row(date(2026, 10, 5), "times_per_week", times=3),
    ]
    shuffled: Sequence[Schedule] = random.Random(seed).sample(rows, k=len(rows))
    assert schedule_on(shuffled, date(2026, 9, 20)) is rows[0]
    assert schedule_on(shuffled, date(2026, 9, 23)) is rows[0]
    assert schedule_on(shuffled, date(2026, 9, 30)) is rows[1]
    assert schedule_on(shuffled, date(2026, 10, 5)) is rows[2]


def test_fr006_schedule_on_reversed_input() -> None:
    first = _row(date(2026, 9, 21), "weekdays", weekdays=21)
    second = _row(date(2026, 9, 24))
    assert schedule_on([second, first], date(2026, 9, 22)) is first
    assert schedule_on([second, first], date(2026, 9, 1)) is first


# --- Rule mapping (R1) --------------------------------------------------------


def test_r1_rule_of_daily_schedule() -> None:
    assert rule_of(_row(date(2026, 9, 21))) == Rule(type="daily")


def test_r1_rule_of_weekdays_schedule_decodes_mask() -> None:
    rule = rule_of(_row(date(2026, 9, 21), "weekdays", weekdays=21))
    assert rule == Rule(type="weekdays", weekdays=frozenset({MON, WED, FRI}))


def test_r1_rule_of_times_per_week_schedule() -> None:
    rule = rule_of(_row(date(2026, 9, 21), "times_per_week", times=3))
    assert rule == Rule(type="times_per_week", times_per_week=3)


def test_r1_rule_defaults_are_empty() -> None:
    rule = Rule(type="daily")
    assert rule.weekdays == frozenset()
    assert rule.times_per_week is None


def test_r1_equal_rules_hash_equal() -> None:
    assert len({MWF, Rule(type="weekdays", weekdays=frozenset({FRI, WED, MON}))}) == 1
