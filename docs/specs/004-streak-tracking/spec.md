# Feature Specification: Streak Tracking

**Feature Branch**: `004-streak-tracking`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Show current and longest streak per habit so users stay motivated."

## Clarifications

### Session 2026-09-26

Resolved by the implementing agent without an interactive session (the requester asked for no interaction); each answer follows the closest existing rule and is flagged for product review.

- Q: How do streaks work for "N times per week" habits (spec 005), where no individual day is required? → A: A week counts as met when it has at least N check-ins. The streak is the number of completed check-ins (at most N per week) across consecutive met weeks plus the current, still-open week; an unmet week breaks the streak only once that week has ended. This mirrors FR-003 ("unscheduled days are skipped, not counted as misses"): after the Nth check-in the rest of the week is unscheduled.
- Q: Do check-ins on unscheduled days (e.g. a Tuesday check-in for a Mon/Wed/Fri habit) extend a streak? → A: No. Streaks count consecutive *scheduled* days completed (FR-001); unscheduled days neither extend nor break a streak.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Current Streak (Priority: P1)

Next to each habit the user sees a flame icon and a number representing consecutive scheduled days completed, ending today or yesterday.

**Why this priority**: Streaks are the primary motivational mechanic of habit trackers.

**Independent Test**: Check in a daily habit three days in a row (via backfill), confirm the streak shows 3.

**Acceptance Scenarios**:

1. **Given** a daily habit completed on the last 3 consecutive days including today, **When** viewing Today, **Then** streak shows 3.
2. **Given** a daily habit completed yesterday but not yet today, **When** viewing Today, **Then** streak still shows the count through yesterday (not broken until the day ends).
3. **Given** a daily habit with a gap two days ago, **When** viewing Today, **Then** the streak counts only days after the gap.

---

### User Story 2 - See Longest Streak (Priority: P2)

On the habit detail view the user sees their all-time longest streak and when it happened.

**Independent Test**: Build a 5-day streak, break it, build a 2-day streak, confirm longest shows 5 with correct date range.

**Acceptance Scenarios**:

1. **Given** streaks of 5 and 2 days in history, **When** viewing habit detail, **Then** longest streak shows 5 with its start and end dates.

---

### User Story 3 - Streaks Respect Schedules (Priority: P2)

A habit scheduled for Mon/Wed/Fri does not break its streak on Tuesday.

**Why this priority**: Without this, non-daily habits are unusable; depends on spec 005.

**Independent Test**: Create a Mon/Wed/Fri habit, complete Mon and Wed, confirm streak is 2 on Thursday.

**Acceptance Scenarios**:

1. **Given** a habit scheduled Mon/Wed/Fri completed Mon and Wed, **When** viewing on Thursday, **Then** streak is 2.
2. **Given** the same habit not completed Friday, **When** viewing on Saturday, **Then** streak is 0.

---

### Edge Cases

- Streak calculation uses the user's timezone for day boundaries.
- Deleting a check-in via undo recalculates streaks immediately.
- A habit created today with one check-in has a streak of 1.
- Archived habits display their frozen streak at archive time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute current streak as consecutive scheduled days completed ending today or the most recent scheduled day.
- **FR-002**: System MUST compute longest streak with its date range.
- **FR-003**: Streak logic MUST honor the habit's schedule (spec 005); unscheduled days are skipped, not counted as misses.
- **FR-004**: Streaks MUST update within the same request cycle as a check-in change (no background job required).
- **FR-005**: Streak values MUST be exposed on the habit list and habit detail API responses.

### Key Entities

- **StreakSummary** (derived, not stored): current length, current start date, longest length, longest start/end dates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Streak computation for a habit with 2 years of daily check-ins completes in under 20 ms.
- **SC-002**: 100% of streak unit tests pass for daily, weekly, and specific-day schedules across timezone boundaries.

## Assumptions

- Streaks are computed on read and cached in memory per request; no denormalized column in v1.
- "Grace period" features (e.g., one free skip per week) are out of scope.
