# Feature Specification: History Calendar

**Feature Branch**: `007-history-calendar`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "A GitHub-style contribution heatmap per habit and for all habits so users can see consistency over time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-Habit Heatmap (Priority: P1)

On a habit's detail page, the user sees the last 12 months as a grid of day cells, shaded by completion (done / not due / missed).

**Why this priority**: Visualizing consistency is the second-biggest motivator after streaks.

**Independent Test**: Check in a habit on 3 scattered dates, open its detail, confirm exactly those 3 cells are filled.

**Acceptance Scenarios**:

1. **Given** a habit with check-ins on 3 dates, **When** viewing its calendar, **Then** those 3 cells are marked done and days not due are neutral.
2. **Given** a cell, **When** hovered or focused, **Then** a tooltip shows the date and status (done / missed / not due).

---

### User Story 2 - Overall Heatmap (Priority: P2)

On the History page, a combined heatmap shades each day by the percentage of due habits completed.

**Independent Test**: Complete 2 of 4 due habits on a date, confirm that day's cell is at the 50% shade level.

**Acceptance Scenarios**:

1. **Given** 2 of 4 due habits completed on a date, **When** viewing the overall heatmap, **Then** the cell reflects 50%.
2. **Given** a day with no due habits, **When** viewing, **Then** the cell is neutral, not "0%".

---

### User Story 3 - Jump to a Day (Priority: P3)

Clicking a cell opens that day in the dashboard (if within 30 days) or a read-only day view (if older).

**Independent Test**: Click a cell 10 days ago, confirm dashboard opens on that date.

**Acceptance Scenarios**:

1. **Given** a cell within 30 days, **When** clicked, **Then** the dashboard shows that date, editable.
2. **Given** a cell older than 30 days, **When** clicked, **Then** a read-only day summary is shown.

---

### Edge Cases

- Color scale must remain distinguishable for color-blind users; use luminance steps plus a pattern or label, not hue alone.
- Heatmap respects the user's week-start setting for column alignment.
- Habits created mid-year show neutral cells before their creation date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide per-habit daily status for any date range up to 366 days in a single request.
- **FR-002**: System MUST provide per-day aggregate completion ratio across active habits for the same range.
- **FR-003**: Heatmap cells MUST be keyboard focusable with an accessible name including date and status.
- **FR-004**: Heatmap MUST distinguish done, missed, and not-due states.
- **FR-005**: Selecting a cell MUST navigate to that day (editable within 30 days, read-only otherwise).

### Key Entities

- **DayStatus** (derived): date, status enum (done, missed, not_due), completion ratio for aggregate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 366-day range API responds in under 200 ms p95 with 10k check-ins.
- **SC-002**: Heatmap renders 366 cells in under 50 ms after data arrives.
- **SC-003**: Passes automated color-contrast checks for all 5 shade levels in light and dark themes.

## Assumptions

- Ranges beyond 12 months are paged by year via a selector; no infinite scroll.
