# Research: Today Dashboard

## R1. Counts on the day summary (FR-002, FR-005)
- **Decision**: `DaySummary` gains `due_count` (items with `status = due`), `completed_count`
  (due items that are completed), and `habit_count` (all active habits, so the UI can tell "no
  habits yet" from "nothing scheduled today"). `done_for_week` items are listed but not counted
  (spec 005 US3-S2). Percentage is `round(100 * completed / due)`, 0 when nothing is due.
- **Alternatives**: separate `/habits` call for the empty state (extra request on every load).

## R2. Optimistic progress
- **Decision**: The optimistic toggle recomputes `completed_count` from the updated items so the
  bar and live region change within the same frame as the tapped control; the refetch in
  `onSettled` restores server truth.

## R3. Live region (FR-006)
- **Decision**: A visually present `<p aria-live="polite">3 of 5 habits done</p>` next to a
  `role="progressbar"` with `aria-valuenow` percent and label "Daily progress". Polite so it never
  interrupts the toggle's own announcement.

## R4. Grouping (US3)
- **Decision**: Two lists, "To do" and "Done" (completed due habits, plus done-for-week habits).
  Rows move immediately (well inside the 300 ms budget). A fade-in was tried and removed: axe
  measured text contrast mid-animation and failed the WCAG AA check.

## R5. Midnight rollover (edge case)
- **Decision**: `useLocalToday(timezone)` re-evaluates `localToday` every 30 s and updates state
  only when the date string changes. Polling avoids DST-sensitive "ms until midnight" math and
  costs one `Intl` call per interval. Only the implicit "today" view follows the rollover; an
  explicit `?date=` stays put.

## R6. Loading state
- **Decision**: `shared/ui/Skeleton` renders placeholder rows inside a container with
  `aria-busy="true"` and a visually hidden "Loading habits" label, replacing the text spinner.

## R7. Performance budget (SC-002)
- **Decision**: Perf test seeds 50 habits × 200 check-ins (10k) and asserts p95 < 150 ms over 30
  requests to `/days/{today}` through the app. Current implementation loads schedules and all
  check-in dates in two queries; no cache needed if the budget holds.
