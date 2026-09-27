# Implementation Plan: Habit Schedules

**Branch**: `005-habit-schedules` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/005-habit-schedules/spec.md`

## Summary

Every habit gets exactly one active schedule: daily (default), specific weekdays, or N times per
week (1–6; 7 normalizes to daily). Schedules are stored as history rows with `effective_from`
so later streak logic (spec 004) can evaluate past dates against the rule active then. A pure
`is_due` function decides due-ness; a new read endpoint `GET /api/v1/days/{date}` exposes which
habits are due (or done for the week) on a local date with their completion state, and the Today
page switches to it. Spec 006 extends the same endpoint with progress counts and UI states.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.9 strict

**Primary Dependencies**: Existing stack. No new dependencies.

**Storage**: SQLite; new `schedule` table (migration `0005`) with a data backfill giving every
existing habit a daily schedule

**Testing**: pytest unit (pure `is_due`, schedule selection, week boundaries) + API; Vitest +
MSW; Playwright @p1 journey

**Target Platform**: Developer laptop, evergreen browsers

**Project Type**: Web application

**Performance Goals**: "Is due" for 50 habits < 10 ms (SC-001); day endpoint < 200 ms p95

**Constraints**: Due-ness uses the user's timezone and Monday week start (spec 012 will make it
configurable); schedule changes never delete check-ins (FR-005)

**Scale/Scope**: ≤ 50 active habits, a handful of schedule rows each

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | No open clarifications. |
| II. Vertical Slices | PASS | Each story ships API + form UI + Today filtering + tests. |
| III. Test-First | PASS | Tests precede implementation in tasks.md. |
| IV. Simplicity | PASS | Weekdays stored as a 7-bit mask; one pure function for due-ness. |
| V. Explicit Contracts | PASS | `contracts/schedules.openapi.yaml`; snapshot + generated types refreshed. |
| VI. Local-First | PASS | No external calls. |
| VII. Human-Accountable | PASS | Commits/PR cite `005` and FR ids. |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
docs/specs/005-habit-schedules/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/schedules.openapi.yaml
```

### Source Code

```text
src/backend/app/
├── models/schedule.py
├── schemas/schedules.py, schemas/days.py
├── services/schedules.py        # pure is_due / schedule_on / week_start + persistence helpers
├── services/days.py             # day summary for a local date
├── services/habits.py           # create/update now manage schedules; returns HabitRead
├── routers/days.py
└── migrations/versions/0005_schedule.py
src/backend/tests/
├── unit/test_schedules.py
└── api/test_schedules_api.py, api/test_days_api.py

src/frontend/src/
├── features/habits/components/SchedulePicker.tsx   # in HabitForm
├── features/habits/schedule-label.ts
├── features/today/                                 # Today uses useDay(date)
├── features/check-ins/hooks/use-check-ins.ts       # optimistic update targets the day query
└── test/day-backend.ts                             # replaces check-ins-backend.ts
src/frontend/e2e/schedules.spec.ts
```

**Structure Decision**: Same web-app layout as earlier specs.

## Complexity Tracking

No violations and no new dependencies.
