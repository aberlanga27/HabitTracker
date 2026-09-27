# Research: Habit Schedules

## R1. Representation
- **Decision**: One `schedule` row per rule change: `type` (`daily | weekdays |
  times_per_week`), `weekdays` 7-bit mask (Mon = bit 0 … Sun = bit 6, `0` unless `weekdays`),
  `times_per_week` (1–6, null unless `times_per_week`), `effective_from` (local date).
  `UNIQUE(habit_id, effective_from)`.
- **Wire**: `{"type": "weekdays", "weekdays": ["mon","wed","fri"]}`, `{"type":
  "times_per_week", "times_per_week": 3}`, `{"type": "daily"}`. Responses always include all
  fields: `weekdays` sorted Monday-first (`[]` when not applicable), `times_per_week` or `null`,
  and `effective_from`.

## R2. Validation (FR-002, FR-003)
- `weekdays` requires at least one day; duplicates collapse.
- `times_per_week` accepts 1–7; `7` is stored as `daily` (spec edge case). Out of range → 422.
- Fields irrelevant to the chosen type are ignored.

## R3. Which schedule applies to a date (FR-006)
- **Decision**: The row with the greatest `effective_from ≤ date`. Dates before the first row use
  the first row, so habits created today can still be backfilled for the 30-day window (spec 003).

## R4. Changing a schedule (FR-005)
- **Decision**: `PATCH /habits/{id}` with `schedule` writes a row effective **today** (user's local
  date). If the latest row is already effective today it is updated in place (several edits in one
  day do not pile up rows); if the new rule equals the current one nothing is written. Check-ins
  are never touched.

## R5. Due-ness (FR-004)
- **daily** → due. **weekdays** → due when the date's weekday is in the set.
- **times_per_week (N)** → let `before` = completed check-ins in the same week strictly before
  the date. Due when `before < N`; otherwise status `done_for_week` (shown, not counted as due —
  US3-S2). This keeps a habit due on the day its Nth check-in happens, so ticking it does not make
  it vanish.
- Week = Monday–Sunday (spec assumption). `TODO(spec-012)` makes week start configurable.
- Pure function `is_due(rule, day, completed_before_in_week) -> bool` in
  `services/schedules.py`; timezone only enters through the local `date` passed in.

## R6. Exposing due-ness: `GET /api/v1/days/{date}`
- **Decision**: Returns `{date, items: [DayHabit]}` for the user's active habits that are `due` or
  `done_for_week` on that local date, ordered by position. `DayHabit = {habit: HabitRead, status,
  completed, note, week}` where `week = {completed, target}` for times-per-week habits (counted
  through the date, e.g. "2 of 3 this week") and `null` otherwise. Unscheduled habits are omitted
  (spec 006: "hidden but reachable from All habits").
- **Rationale**: The Today page needs due-ness and completion together; spec 006 will add
  progress counts to the same response (architecture: `/days/{date}`), so this avoids a
  throwaway endpoint.
- `GET /check-ins?date=` from spec 003 stays for simple clients; the frontend no longer uses it.

## R7. `HabitRead.schedule`
- **Decision**: Every habit response includes the schedule active on the user's local today. Lists
  load schedules for all listed habits in one query (no N+1).

## R8. Migration
- **Decision**: `0005` creates `schedule` and inserts a daily row for each existing habit with
  `effective_from = date(created_at)`, satisfying FR-001 ("every habit has exactly one schedule").
