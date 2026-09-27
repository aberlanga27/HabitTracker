# Data Model: Habit Schedules

## Schedule (`schedule`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| habit_id | str | FK → habit.id ON DELETE CASCADE, indexed |
| type | str | `daily`, `weekdays`, or `times_per_week` |
| weekdays | int | 7-bit mask, Mon = 1 … Sun = 64; `> 0` iff `type = weekdays` |
| times_per_week | int \| null | 1–6 iff `type = times_per_week` (7 is stored as `daily`) |
| effective_from | date | local date the rule starts applying |

Constraints: `UNIQUE(habit_id, effective_from)`.

## Selection rule

`schedule_on(date)` = row with max `effective_from ≤ date`, else the earliest row.

## Derived: DayHabit (API only)

| Field | Meaning |
|---|---|
| habit | `HabitRead` (includes current `schedule`) |
| status | `due` or `done_for_week` |
| completed | a check-in exists on the date |
| note | that check-in's note or null |
| week | `{completed, target}` for times-per-week (through the date), else null |

## State transitions

```
create habit ──> schedule(effective_from = today, daily unless given)
change schedule ──> same-day row updated, otherwise new row effective today
delete habit ──> schedules cascade
```
