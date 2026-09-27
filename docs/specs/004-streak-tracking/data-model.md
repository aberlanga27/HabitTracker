# Data Model: Streak Tracking

No tables change. Streaks are derived on read (ADR-3).

## Derived: StreakSummary (`HabitRead.streak`)

| Field | Type | Meaning |
|---|---|---|
| current | int ≥ 0 | consecutive scheduled days completed, ending today (pending) or the most recent scheduled day |
| current_start | date \| null | first date of the current run; null when `current = 0` |
| longest | int ≥ 0 | longest run ever (≥ current) |
| longest_start | date \| null | first completed date of the longest run |
| longest_end | date \| null | last completed date of the longest run |

## Inputs

- Schedule history rows (spec 005) → rule per date.
- Set of completed local dates (spec 003 check-ins).
- End date: user's local today, or the local date of `archived_at` for archived habits.
