# Research: Streak Tracking

## R1. Algorithm
- **Decision**: `compute_streak(schedules, completed, today, frozen_at=None) -> Streak` walks
  each local date from the earlier of (first schedule's `effective_from`, earliest check-in) to
  the end date (`frozen_at` for archived habits, else `today`), using `schedule_on(date)` (spec 005
  FR-006) for the rule of that day. O(days) with set lookups: 2 years ≈ 730 iterations, far below
  the 20 ms budget.
- **daily / weekdays**: a scheduled day completed extends the run (recording its start); a
  scheduled day missed resets it — except the end date, which is still in progress (US1-S2).
  Unscheduled days are skipped (FR-003) and unscheduled check-ins are ignored (Clarifications).
- **times_per_week (N)**: a day counts while it is due (fewer than N completions earlier that
  week); completions on due days extend the run. When a week ends (Sunday strictly before the end
  date) with fewer than N completions the run resets. The current open week never breaks the run
  (Clarifications).
- **Longest**: the maximum run seen, with first and last completed dates; ties keep the earliest.

## R2. End date
- **Decision**: `today` = the user's local date; archived habits use the local date of
  `archived_at` so their streak is frozen (edge case). Current streak for an archived habit is the
  run at that date.

## R3. Exposure (FR-005)
- **Decision**: `HabitRead.streak = {current, current_start, longest, longest_start,
  longest_end}` on every habit response: list, detail, mutations, and each `DayHabit.habit` in
  `/days/{date}`. `read_many` loads schedules and check-in dates for all listed habits in two
  queries. FR-004 holds because values are derived per request.

## R4. Viewer dependency
- **Decision**: Replace `TodayDep` with `ViewerDep` (`user_id`, `timezone`, `today`) so services
  can freeze archived streaks in the user's timezone without re-reading the user.

## R5. UI
- **Decision**: `StreakBadge` renders "🔥 3" with an accessible name "Current streak: 3 days"
  (emoji `aria-hidden`), shown on Today rows and the habits list. A habit detail route
  `/habits/:id` shows current and longest streak with its date range (US2). The habit name in the
  list links to it.
