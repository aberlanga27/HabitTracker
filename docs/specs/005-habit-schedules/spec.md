# Feature Specification: Habit Schedules

**Feature Branch**: `005-habit-schedules`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Habits can be daily, on specific weekdays, or N times per week, so the Today view only shows what is due."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily Schedule (Default) (Priority: P1)

Every new habit defaults to "every day". The user can leave it as-is and see it on Today every day.

**Why this priority**: The default path must work with zero configuration.

**Independent Test**: Create a habit without touching schedule, confirm it shows every day for a week.

**Acceptance Scenarios**:

1. **Given** the new-habit form, **When** submitted without changing schedule, **Then** the habit is due every day.

---

### User Story 2 - Specific Weekdays (Priority: P1)

A user sets a habit to Mon/Wed/Fri. It appears on Today only on those days.

**Why this priority**: Most real habits (gym, classes) are not daily.

**Independent Test**: Set Mon/Wed/Fri, navigate to a Tuesday, confirm absent; a Wednesday, confirm present.

**Acceptance Scenarios**:

1. **Given** a habit set to Mon/Wed/Fri, **When** viewing a Tuesday, **Then** the habit is not listed as due.
2. **Given** the schedule form, **When** no weekday is selected, **Then** validation prevents saving.

---

### User Story 3 - N Times per Week (Priority: P2)

A user sets "3 times per week". The habit appears every day until 3 check-ins are logged that week, then shows as "done for this week".

**Independent Test**: Set 3x/week, check in Mon/Tue/Wed, confirm Thursday shows "done for the week".

**Acceptance Scenarios**:

1. **Given** a 3x/week habit with 2 check-ins this week, **When** viewing Today, **Then** it is due and shows "2 of 3 this week".
2. **Given** 3 check-ins this week, **When** viewing Today, **Then** it shows completed-for-week and is not counted as due.

---

### User Story 4 - Change Schedule Safely (Priority: P3)

A user changes a habit's schedule; past streaks are not retroactively recomputed against the new schedule in a way that penalizes them.

**Independent Test**: Build a Mon/Wed/Fri streak of 3, switch to daily, confirm streak does not drop to 0.

**Acceptance Scenarios**:

1. **Given** a schedule change, **When** saved, **Then** the new schedule applies from today forward and previous streak history is preserved.

---

### Edge Cases

- Week starts on Monday by default; configurable in settings (spec 012).
- Changing timezone shifts which local weekday a date falls on; schedule evaluation always uses the user's current timezone.
- A habit scheduled 7 times per week is equivalent to daily.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every habit MUST have exactly one schedule of type daily, weekdays, or times-per-week.
- **FR-002**: Weekday schedules MUST require at least one selected day.
- **FR-003**: Times-per-week schedules MUST accept 1–6 (7 is normalized to daily).
- **FR-004**: System MUST expose whether a habit is "due" on a given local date.
- **FR-005**: Schedule changes MUST be effective from the current date and MUST NOT delete existing check-ins.
- **FR-006**: Schedule history MUST be retained so streaks (spec 004) evaluate past dates against the schedule active at that time.

### Key Entities

- **Schedule**: Belongs to one Habit. Attributes: type, weekday set (for weekdays), target count (for times-per-week), effective-from date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: "Is due today" evaluation for 50 habits completes in under 10 ms.
- **SC-002**: Schedule change preserves 100% of check-ins and streak history in tests.

## Assumptions

- Monthly or interval schedules ("every 3 days") are out of scope for v1.
- Week boundary defaults to Monday.
