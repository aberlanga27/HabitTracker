# Data Model: Daily Check-In

## CheckIn (`check_in`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| habit_id | str | FK → habit.id ON DELETE CASCADE |
| local_date | date | the user's local calendar date the check-in belongs to |
| completed_at | datetime (UTC) | when the first completion for that date was recorded |
| note | str \| null | trimmed, ≤ 280 chars, empty → null |

Constraints: `UNIQUE(habit_id, local_date)` (FR-004); index on `(habit_id, local_date)` serves
both uniqueness and range reads.

## Derived: CheckInState (API only)

`{habit_id, date, completed, note, completed_at}`; `completed=false` implies `note=null` and
`completed_at=null`.

## Rules

- Editable dates: `today - 30 ≤ date ≤ today` in the user's timezone (FR-002, FR-003, FR-007).
- Habit must be owned by the user (404 otherwise) and active (409 `HABIT_ARCHIVED` otherwise).
- Deleting a habit deletes its check-ins (cascade, spec 002 FR-004).
