# Data Model: Today Dashboard

No tables change.

## Derived: DaySummary (`GET /api/v1/days/{date}`)

| Field | Type | Meaning |
|---|---|---|
| date | date | the requested local date |
| items | DayHabit[] | due and done-for-week habits, ordered by position (spec 005) |
| due_count | int | items with `status = due` |
| completed_count | int | due items that are completed |
| habit_count | int | all active habits of the user (empty-state detection) |

Percentage (UI) = `round(100 × completed_count / due_count)`, `0` when `due_count = 0`.

## UI states

| Condition | State |
|---|---|
| `habit_count = 0` | Empty: "Create your first habit" |
| `due_count = 0`, `habit_count > 0` | Nothing scheduled for this day |
| `due_count > 0`, `completed_count = due_count` | All done: "All done for today" |
| otherwise | Progress "c of d done", To do + Done sections |
