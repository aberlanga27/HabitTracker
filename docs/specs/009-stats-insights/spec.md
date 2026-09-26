# Feature Specification: Stats & Insights

**Feature Branch**: `009-stats-insights`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Show completion rates, best weekday, totals and a simple trend so users understand how consistent they are."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-Habit Completion Rate (Priority: P1)

On a habit's detail page the user sees the completion rate for the last 7, 30, and 90 days, computed as completed scheduled days divided by scheduled days in the window.

**Why this priority**: Completion rate is the most honest consistency signal and complements streaks (spec 004), which reset to zero on a single miss.

**Independent Test**: Create a daily habit, backfill 5 of the last 7 days, open detail, confirm the 7-day rate reads 71%.

**Acceptance Scenarios**:

1. **Given** a daily habit completed on 5 of the last 7 days, **When** viewing its detail, **Then** the 7-day rate shows 71% (5 of 7).
2. **Given** a Mon/Wed/Fri habit (spec 005) completed on all 3 scheduled days this week, **When** viewing the 7-day rate, **Then** it shows 100%, not 43%.
3. **Given** a habit created 3 days ago, **When** viewing the 30-day rate, **Then** the denominator is the 3 scheduled days since creation, and the card notes "since creation".

---

### User Story 2 - Overall Completion Rate (Priority: P1)

On the Stats page the user sees the overall completion rate across all active habits for the same 7/30/90-day windows, plus total check-ins all-time.

**Why this priority**: Gives a single number to answer "how am I doing?" without opening each habit.

**Independent Test**: With 2 daily habits, complete both today and one yesterday, confirm the 7-day overall rate reflects 3 of 4 scheduled slots for those two days (plus zeros for earlier days).

**Acceptance Scenarios**:

1. **Given** 2 daily habits with 3 of 14 scheduled slots completed in the last 7 days, **When** viewing Stats, **Then** the overall 7-day rate shows 21%.
2. **Given** no active habits, **When** viewing Stats, **Then** an empty state explains that stats appear after the first check-in.
3. **Given** 120 all-time check-ins, **When** viewing Stats, **Then** "Total check-ins: 120" is shown.

---

### User Story 3 - Best Weekday (Priority: P2)

The Stats page highlights the weekday with the highest completion rate over the last 90 days (e.g. "You're strongest on Tuesdays: 88%").

**Why this priority**: Actionable insight users can plan around; low effort once rates exist.

**Independent Test**: Backfill check-ins so Tuesdays are always completed and other days are not, confirm "Tuesday" is reported as best.

**Acceptance Scenarios**:

1. **Given** Tuesday has the highest completion ratio over 90 days, **When** viewing Stats, **Then** Tuesday is labeled best weekday with its percentage.
2. **Given** two weekdays tie, **When** viewing Stats, **Then** the earlier weekday in the user's week-start order (spec 012) is shown and the tie is noted.
3. **Given** fewer than 14 days of history, **When** viewing Stats, **Then** best weekday shows "Not enough data yet".

---

### User Story 4 - Simple Trend (Priority: P3)

The Stats page shows whether the last 30 days are better, worse, or about the same as the 30 days before, as an arrow and a percentage-point delta.

**Why this priority**: Motivational nudge; depends on everything above being correct first.

**Independent Test**: Backfill 60 days with 50% completion in the older window and 80% in the newer window, confirm the trend shows "+30 pts".

**Acceptance Scenarios**:

1. **Given** 80% in the last 30 days and 50% in the prior 30, **When** viewing Stats, **Then** the trend shows an upward arrow and "+30 pts".
2. **Given** a delta within ±3 points, **When** viewing Stats, **Then** the trend is labeled "Steady".
3. **Given** fewer than 60 days of history, **When** viewing Stats, **Then** the trend card shows "Not enough data yet".

---

### Edge Cases

- Windows are computed in the user's timezone (spec 012) and end on the current local date, inclusive.
- Days on which a habit is not due (spec 005) are excluded from both numerator and denominator.
- Archived habits are excluded from overall stats but their own detail page still shows historical rates, frozen at the archive date.
- A habit with zero scheduled days in a window shows "—" rather than 0% or a division error.
- Backfilled check-ins (spec 003) count identically to same-day check-ins.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute per-habit completion rate for 7, 30, and 90-day windows as completed scheduled days ÷ scheduled days.
- **FR-002**: System MUST compute the overall completion rate across active habits for the same windows.
- **FR-003**: System MUST report total all-time check-ins per habit and overall.
- **FR-004**: System MUST identify the best weekday over the last 90 days, with a minimum of 14 days of history.
- **FR-005**: System MUST compute a 30-day-vs-prior-30-day trend delta in percentage points, with a minimum of 60 days of history.
- **FR-006**: Stats MUST respect each habit's schedule history (spec 005) and the user's timezone and week-start settings (spec 012).
- **FR-007**: Stats MUST be exposed via the API for a habit and for the user, each in a single request.

### Key Entities

- **HabitStats** (derived, not stored): habit id, rates for 7/30/90 days (completed, scheduled, ratio), total check-ins.
- **UserStats** (derived, not stored): overall rates for 7/30/90 days, total check-ins, best weekday with ratio, trend delta and label.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User stats API responds in under 200 ms p95 with 50 habits and 10k check-ins.
- **SC-002**: Per-habit stats API responds in under 50 ms p95 with 2 years of daily check-ins.
- **SC-003**: 100% of rate calculations match a reference implementation in property-based tests across daily, weekday, and times-per-week schedules.
- **SC-004**: Stats page renders all cards in under 100 ms after data arrives.

## Assumptions

- Stats are computed on read; no nightly aggregation job in v1.
- Charts beyond the heatmap (spec 007) are out of scope; stats are numeric cards.
- Times-per-week habits count each week as one scheduled unit with a fractional completion (check-ins ÷ target, capped at 1).
