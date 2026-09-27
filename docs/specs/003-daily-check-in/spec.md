# Feature Specification: Daily Check-In

**Feature Branch**: `003-daily-check-in`

**Created**: 2026-09-26

**Status**: Implemented

**Input**: User description: "Users mark a habit as done (or undo it) for today or a past day, with a quick one-tap interaction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check In for Today (Priority: P1)

A user taps a habit on the Today view to mark it complete. The habit shows a completed state instantly and the change persists.

**Why this priority**: This is the single most frequent interaction in the app and the reason it exists.

**Independent Test**: Tap a habit, reload, confirm still completed; tap again, reload, confirm uncompleted.

**Acceptance Scenarios**:

1. **Given** an uncompleted habit for today, **When** the user taps it, **Then** it is marked complete with visual feedback within 100 ms and persisted.
2. **Given** a completed habit for today, **When** the user taps it, **Then** the completion is removed (undo).
3. **Given** a network failure during save, **When** the user taps a habit, **Then** the UI reverts to the previous state and shows a non-blocking error.

---

### User Story 2 - Backfill a Past Day (Priority: P2)

A user forgot to log yesterday. They navigate to a past date (up to 30 days back) and mark the habit complete for that day.

**Why this priority**: Missed logging is common; without backfill, streaks break unfairly and users churn.

**Independent Test**: Go to yesterday, check in a habit, return to Today, confirm streak reflects it.

**Acceptance Scenarios**:

1. **Given** a habit, **When** the user selects yesterday and marks it complete, **Then** a check-in for that date is stored.
2. **Given** a date more than 30 days ago, **When** the user tries to check in, **Then** the control is disabled with an explanation.
3. **Given** a future date, **When** the user tries to check in, **Then** the control is disabled.

---

### User Story 3 - Add a Note to a Check-In (Priority: P3)

A user attaches a short note ("ran 5k in the rain") to a check-in.

**Independent Test**: Check in, add a note, reopen the day, confirm the note is shown.

**Acceptance Scenarios**:

1. **Given** a completed check-in, **When** the user adds a note up to 280 characters, **Then** it is saved and visible on that day.

---

### Edge Cases

- "Today" is computed in the user's timezone, not the server's; a check-in at 23:59 local counts for that local date.
- Double-tapping quickly must not create duplicate check-ins; one check-in per habit per date.
- Archived habits cannot receive new check-ins.
- Offline taps queue and retry when connectivity returns (v1 may simply fail gracefully; see Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to toggle completion of an active habit for the current local date with one interaction.
- **FR-002**: Users MUST be able to toggle completion for any date within the past 30 days.
- **FR-003**: System MUST reject check-ins for future dates or dates older than 30 days.
- **FR-004**: System MUST enforce at most one check-in per habit per date.
- **FR-005**: Users MUST be able to attach an optional note (≤280 chars) to a check-in.
- **FR-006**: UI MUST apply optimistic updates and roll back on failure.
- **FR-007**: System MUST interpret dates in the user's stored timezone.

### Key Entities

- **CheckIn**: Belongs to one Habit. Attributes: local date (YYYY-MM-DD), completed-at timestamp, optional note. Unique on (habit, date).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A check-in reflects in the UI within 100 ms of tap (optimistic).
- **SC-002**: Zero duplicate check-ins under a 20-tap rapid-fire automated test.
- **SC-003**: 95% of users complete their first check-in without instructions in usability testing.

## Assumptions

- Offline queueing is out of scope for v1; failed saves show an error and revert.
- Habits are binary (done / not done); quantity-based habits are a possible future spec.
