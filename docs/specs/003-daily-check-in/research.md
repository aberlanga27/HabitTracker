# Research: Daily Check-In

## R1. Toggle shape
- **Decision**: `PUT /api/v1/habits/{habit_id}/check-ins/{date}` with `{"completed": bool,
  "note"?: string | null}` sets the state idempotently and returns the resulting
  `CheckInState`. `completed=false` deletes the row (undo). Repeating a request is harmless,
  which is what makes 20 rapid taps safe (SC-002).
- **Alternatives**: `POST` + `DELETE` pair (not idempotent; double taps race into duplicates or
  404s).

## R2. Duplicate prevention (FR-004)
- **Decision**: `UNIQUE(habit_id, local_date)` plus SQLite
  `INSERT … ON CONFLICT(habit_id, local_date) DO NOTHING`. The first write sets `completed_at`;
  later identical writes keep it. The UI also disables a habit's control while its mutation is
  pending.

## R3. Editable window (FR-002, FR-003, FR-007)
- **Decision**: `today = local_date(clock.now(), user.timezone)`. A date is editable when
  `today - 30 days ≤ date ≤ today`. Outside → `422 DATE_OUT_OF_RANGE` with
  `details = {"earliest": ..., "latest": ...}`. The window check lives in one pure function,
  `editable_window(today) -> (earliest, latest)`, reused by the UI rules via the same constants.
- The frontend derives the user's local today with `Intl.DateTimeFormat` in the stored timezone
  (from `/auth/me`), mirroring the server; the server remains the authority.

## R4. Archived habits
- **Decision**: Toggling or editing a note on an archived habit → `409 HABIT_ARCHIVED`
  "Archived habits cannot be checked in". Archived means frozen, so undo is blocked too.

## R5. Note (FR-005)
- **Decision**: Optional, trimmed, ≤ 280 chars, empty → `null`. Only stored on a completed
  check-in; sending a note with `completed=false` is ignored because the row is removed. When
  `note` is omitted the existing note is kept.

## R6. Reading state for a day
- **Decision**: `GET /api/v1/check-ins?date=YYYY-MM-DD` returns the user's check-ins for that
  date `{items: [CheckInState], total}`. Spec 006 adds the full day summary; this endpoint keeps
  003 independently shippable and stays useful for simple clients.

## R7. Optimistic UI (FR-006)
- **Decision**: TanStack Query `onMutate` writes the new state into `['check-ins', date]`,
  `onError` restores the snapshot and shows a non-blocking `role="status"` message
  "Could not save. Please try again.", `onSettled` invalidates `['check-ins']` and `['habits']`.
  Pattern from docs/frontend.md.

## R8. Day navigation for backfill (US2)
- **Decision**: The Today page reads `?date=YYYY-MM-DD` (URL is state, docs/frontend.md) with
  Previous / Next / Today buttons bounded to the editable window. Dates outside the window
  (hand-typed URL) render controls disabled with an explanation. Spec 006 builds on this.

## R9. Control semantics
- **Decision**: Each habit is a `<button aria-pressed>` whose accessible name is the habit name;
  completed state is also shown with a ✓ glyph so color is not the only signal.
