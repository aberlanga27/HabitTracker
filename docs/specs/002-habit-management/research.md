# Research: Habit Management

## R1. Palette values
- **Decision**: `color` is one of `coral, amber, lime, teal, sky, indigo, violet, rose`, mapping
  to design tokens `--habit-1` … `--habit-8` (docs/frontend.md). Default `coral` when omitted.
- **Rationale**: Named values are stable on the wire and independent of the token numbering.

## R2. Icon
- **Decision**: Optional string of 1–16 characters containing no ASCII letters, digits, or
  whitespace. The UI offers a fixed emoji picker; the API check keeps free text out without an
  emoji-parsing dependency. 16 characters covers multi-code-point emoji (ZWJ sequences, flags).

## R3. Name and description
- **Decision**: Name trimmed, then 1–80 characters; description trimmed, ≤ 500, empty → `null`.
  Names are not unique (edge case in spec).

## R4. Active-habit limit (FR-006)
- **Decision**: Creating or restoring a habit when the user already has 50 active habits fails
  with `409 HABIT_LIMIT_REACHED` "Habit limit reached (50)", `details.limit = 50`. Archived
  habits do not count.

## R5. Ordering (FR-005)
- **Decision**: Integer `position`. New and restored habits append (`max + 1`).
  `PUT /api/v1/habits/order` takes the full ordered list of the user's **active** habit ids and
  rewrites positions `0..n-1`; a list that is not exactly that set is `422`. Lists sort by
  `position`, then `created_at`.
- **UI**: "Move up" / "Move down" buttons on each row work for both pointer and keyboard, which is
  what FR-005 requires. Drag-and-drop from the story text is deferred: it needs either a library
  (Principle IV) or a sizable custom implementation for no extra capability.

## R6. Archive / restore
- **Decision**: `POST /habits/{id}/archive` sets `archived_at = now`; `POST /habits/{id}/restore`
  clears it and appends the habit. Both are idempotent. Verb sub-resources follow the state
  transition exception in coding-standards §4.

## R7. Delete with typed confirmation (FR-004)
- **Decision**: The typed-name confirmation is a UI gate (inline confirm panel with a text field;
  the Delete button stays disabled until the typed value matches the habit name). The API
  `DELETE /habits/{id}` is a plain `204`. Check-ins, schedules, and reminders introduced by later
  specs cascade via `ON DELETE CASCADE`.

## R8. Ownership (FR-007)
- **Decision**: Every service query filters by `user_id`; a missing or foreign id is
  `404 NOT_FOUND` "Habit not found" (architecture: 404 rather than 403 to avoid enumeration).

## R9. Interim Today view
- **Decision**: Until spec 006, `/` lists active habits in order with an empty-state link
  "Create your first habit". This satisfies US3-S1 ("no longer appears in Today") without
  pre-building the day summary.
