---
description: "Task list for spec 005 Habit Schedules"
---

# Tasks: Habit Schedules

**Input**: Design documents from `docs/specs/005-habit-schedules/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/schedules.openapi.yaml

**Tests**: Required (constitution Principle III). Tests are written first and must fail.

Stories: US1 Daily default, US2 Specific weekdays, US3 N times per week, US4 Change schedule safely.

## Phase 1: Setup

- [X] T001 Confirm no new dependencies (plan.md) and branch `005-habit-schedules` is based on `main`

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 `Schedule` model (`type`, `weekdays` mask, `times_per_week` 1–6 nullable, `effective_from` date, FK habit ON DELETE CASCADE, `UNIQUE(habit_id, effective_from)`) in src/backend/app/models/schedule.py
- [X] T003 Migration `0005` creating `schedule` and backfilling a daily row per existing habit in src/backend/app/migrations/versions/0005_schedule.py
- [X] T004 [P] Unit tests for `is_due`, `schedule_on`, `week_start` (Monday), mask round-trip, 7× → daily, week spanning month/year, DST day in src/backend/tests/unit/test_schedules.py
- [X] T005 Pure schedule functions and persistence helpers in src/backend/app/services/schedules.py
- [X] T006 Schemas `ScheduleIn` (FR-002, FR-003 validation), `ScheduleRead`; `HabitCreate.schedule`, `HabitUpdate.schedule`, `HabitRead.schedule` in src/backend/app/schemas/schedules.py and src/backend/app/schemas/habits.py
- [X] T007 [P] `DayHabit`, `DaySummary`, `WeekProgress` schemas in src/backend/app/schemas/days.py
- [X] T008 [P] MSW day backend (GET `/days/:date`, PUT check-ins) replacing check-ins-backend in src/frontend/src/test/day-backend.ts

## Phase 3: User Story 1 - Daily Schedule (Default) (P1) 🎯 MVP

### Tests (write first)

- [X] T009 [P] [US1] API tests: habit created without schedule has `{"type":"daily"}` effective today (user tz) and is in `/days/{date}` every day of a week; existing habits after migration are daily (FR-001, FR-004) in src/backend/tests/api/test_schedules_api.py and src/backend/tests/api/test_days_api.py
- [X] T010 [P] [US1] Component tests: schedule picker defaults to "Every day"; list shows "Every day" in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [X] T011 [US1] Habit service creates the initial schedule and returns `HabitRead` with current schedule (single query for lists) in src/backend/app/services/habits.py and src/backend/app/routers/habits.py
- [X] T012 [US1] Day summary service and `GET /api/v1/days/{date}` in src/backend/app/services/days.py and src/backend/app/routers/days.py
- [X] T013 [US1] Export OpenAPI and regenerate types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [X] T014 [US1] Today page reads `useDay(date)`; toggle optimistically updates the day query in src/frontend/src/features/today/ and src/frontend/src/features/check-ins/hooks/use-check-ins.ts

## Phase 4: User Story 2 - Specific Weekdays (P1) 🎯 MVP

### Tests (write first)

- [X] T015 [P] [US2] API tests: Mon/Wed/Fri habit absent from a Tuesday and present on a Wednesday `/days/{date}`; empty weekday set → 422 and nothing saved; weekday of a date follows user tz (FR-002, FR-004) in src/backend/tests/api/test_schedules_api.py and src/backend/tests/api/test_days_api.py
- [X] T016 [P] [US2] Component tests: choosing "Specific days" reveals labelled weekday checkboxes; none ticked shows "Choose at least one day" and sends nothing; list shows "Mon, Wed, Fri" in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [X] T017 [US2] `SchedulePicker` in `HabitForm` and `scheduleLabel` in src/frontend/src/features/habits/components/SchedulePicker.tsx and src/frontend/src/features/habits/schedule-label.ts

## Phase 5: User Story 3 - N Times per Week (P2)

### Tests (write first)

- [X] T018 [P] [US3] API tests: 3×/week with 2 check-ins this week → `due`, `week = {completed: 2, target: 3}`; with 3 before the date → `done_for_week`; the day of the 3rd check-in stays `due` + completed; weeks reset on Monday; 7 → daily; 0 or 8 → 422 (FR-003, FR-004) in src/backend/tests/api/test_days_api.py
- [X] T019 [P] [US3] Component tests: Today shows "2 of 3 this week" and "Done for this week" in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [X] T020 [US3] Week progress and done-for-week labels on `CheckInRow` in src/frontend/src/features/check-ins/components/CheckInRow.tsx

## Phase 6: User Story 4 - Change Schedule Safely (P3)

### Tests (write first)

- [X] T021 [P] [US4] API tests: PATCH schedule writes a row effective today, past dates still use the old rule in `/days/{date}`, same-day edits update in place, unchanged rule writes nothing, check-ins untouched (FR-005, FR-006) in src/backend/tests/api/test_schedules_api.py
- [X] T022 [P] [US4] Component test: editing a habit's schedule sends `schedule` in the PATCH in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [X] T023 [US4] `set_schedule` on update in src/backend/app/services/habits.py and src/backend/app/services/schedules.py

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T024 [P] SC-001 perf test: due evaluation for 50 habits < 10 ms (marker `perf`) in src/backend/tests/perf/test_perf_schedules.py
- [X] T025 [P] Playwright @p1 journey: Mon/Wed/Fri habit hidden on a non-scheduled day, visible on a scheduled day, validation error for no days, axe in src/frontend/e2e/schedules.spec.ts
- [X] T026 Remove the frontend's unused per-date check-ins query (`useCheckIns`, `listCheckIns`) now that Today uses the day summary in src/frontend/src/features/check-ins/
- [X] T027 Mark spec Implemented in docs/specs/005-habit-schedules/spec.md and docs/specs/README.md
- [X] T028 Run quickstart.md validation

## Dependencies & Execution Order

Foundational (T002–T008) → US1 → US2 → US3 → US4 → Polish. All stories share
`services/habits.py`, `services/days.py`, and `HabitForm`, so they run sequentially.

## Implementation Strategy

MVP = US1 + US2 (both P1). US3 (P2) and US4 (P3) ship in the same PR because the day summary and
schedule history they need are built for US1 anyway.
