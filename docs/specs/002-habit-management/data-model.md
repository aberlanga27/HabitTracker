# Data Model: Habit Management

## Habit (`habit`)

| Field | Type | Constraints |
|---|---|---|
| id | str (UUIDv7) | PK |
| user_id | str | FK → user.id ON DELETE CASCADE, indexed |
| name | str | trimmed, 1–80 chars, not unique |
| description | str \| null | trimmed, ≤ 500 chars, empty → null |
| icon | str \| null | 1–16 chars, no ASCII letters/digits/whitespace |
| color | str | enum `coral, amber, lime, teal, sky, indigo, violet, rose`; default `coral` |
| position | int | ≥ 0; order among the user's habits |
| archived_at | datetime (UTC) \| null | null = active |
| created_at | datetime (UTC) | required |

Index: `(user_id, archived_at)` for the list query.

## State transitions

```
active --archive--> archived --restore--> active (appended to end)
active|archived --delete--> (gone, cascades to dependent rows)
```

## Rules

- At most 50 active habits per user (create and restore check).
- All reads and writes filter by `user_id`.
