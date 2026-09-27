# Feature Specification: Today Dashboard

**Feature Branch**: `006-today-dashboard`

**Created**: 2026-09-26

**Status**: Implemented

**Input**: User description: "A home screen that shows what is due today, progress for the day, and lets the user check in quickly."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Today at a Glance (Priority: P1)

On opening the app, the user sees today's date, a progress bar ("3 of 5 done"), and the list of due habits ordered by their sort position, with completed ones visually distinct.

**Why this priority**: This is the app's landing screen and where every daily interaction starts.

**Independent Test**: Sign in with 5 habits due, complete 3, confirm progress reads "3 of 5" and the bar is 60% filled.

**Acceptance Scenarios**:

1. **Given** 5 due habits with 3 complete, **When** the dashboard loads, **Then** progress shows "3 of 5" and 60%.
2. **Given** zero habits, **When** the dashboard loads, **Then** an empty state with a "Create your first habit" call-to-action is shown.
3. **Given** all habits complete, **When** the dashboard loads, **Then** a celebratory "All done for today" message is shown.

---

### User Story 2 - Navigate Between Days (Priority: P2)

The user moves to yesterday or earlier (up to 30 days) with previous/next controls and sees that day's due habits and completion state.

**Independent Test**: Press "previous day", confirm header shows yesterday and check-in state for that date.

**Acceptance Scenarios**:

1. **Given** the Today view, **When** the user presses previous, **Then** the view shows yesterday with its own completion state.
2. **Given** a past date, **When** the user presses "Today", **Then** the view returns to the current date.

---

### User Story 3 - Group by Completion (Priority: P3)

Completed habits sink to a "Done" section so the remaining list is short.

**Independent Test**: Complete one habit, confirm it moves to the Done section without page reload.

**Acceptance Scenarios**:

1. **Given** a due habit, **When** it is completed, **Then** it animates to the Done section within 300 ms.

---

### Edge Cases

- Habits not due today (per schedule) are hidden but reachable from the "All habits" page.
- The date header updates at local midnight without reload if the tab stays open.
- Loading state shows skeletons, not a spinner, to avoid layout shift.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dashboard MUST list only habits due on the selected local date, ordered by sort position.
- **FR-002**: Dashboard MUST show a completion ratio and percentage for the selected date.
- **FR-003**: Users MUST be able to toggle check-ins directly from the dashboard (spec 003).
- **FR-004**: Users MUST be able to navigate to any of the previous 30 days and back to today.
- **FR-005**: Dashboard MUST render an empty state and an all-done state.
- **FR-006**: Dashboard MUST be fully operable via keyboard and announce progress changes to screen readers.

### Key Entities

- **DaySummary** (derived): date, due habits with completion flags, completed count, due count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard first contentful paint under 1.5 s on a cold local load.
- **SC-002**: Day summary API responds in under 150 ms p95 with 50 habits and 10k check-ins.
- **SC-003**: Lighthouse accessibility score ≥ 95.

## Assumptions

- Mobile-first responsive layout; a single column on narrow screens.
- No widgets or OS-level integrations in v1.
