---
description: "Task list for spec 003 Daily Check-In"
---

# Tasks: Daily Check-In

**Input**: Design documents from `docs/specs/003-daily-check-in/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/check-ins.openapi.yaml

**Tests**: Required (constitution Principle III). Tests are written first and must fail.

Stories: US1 Check in for today, US2 Backfill a past day, US3 Add a note.

## Phase 1: Setup

- [ ] T001 Confirm no new dependencies (plan.md) and branch `003-daily-check-in` is based on `main`

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 `CheckIn` model (`local_date` date, `completed_at` UTC, `note` ≤ 280 nullable, FK habit ON DELETE CASCADE, `UNIQUE(habit_id, local_date)`) in src/backend/app/models/check_in.py
- [ ] T003 Migration `0004` creating `check_in` in src/backend/app/migrations/versions/0004_check_in.py
- [ ] T004 [P] `make_check_in` factory in src/backend/tests/factories.py
- [ ] T005 [P] Unit tests for `editable_window(today)` (today-30 .. today) and `is_editable` in src/backend/tests/unit/test_check_in_window.py
- [ ] T006 [P] Frontend date helpers `localToday(tz, now)`, `addDays`, `formatDayLabel` with tests (23:59 local, east-of-UTC) in src/frontend/src/shared/lib/dates.ts and src/frontend/src/shared/lib/dates.test.ts
- [ ] T007 [P] In-memory MSW check-ins backend in src/frontend/src/test/check-ins-backend.ts

## Phase 3: User Story 1 - Check In for Today (P1) 🎯 MVP

**Goal**: One tap toggles today's completion, instantly and persistently.

**Independent Test**: Tap, reload, still completed; tap again, reload, uncompleted.

### Tests (write first)

- [ ] T008 [P] [US1] API tests: PUT completed=true creates, repeat keeps one row and original `completed_at` (FR-001, FR-004, SC-002 with 20 rapid PUTs); completed=false undoes; GET `/check-ins?date=` lists state; today computed in user tz incl. 23:59 local (FR-007); foreign habit 404; archived habit 409 `HABIT_ARCHIVED`; rename keeps check-ins (002 SC-002); deleting a habit cascades in src/backend/tests/api/test_check_ins_api.py
- [ ] T009 [P] [US1] Component tests: tapping marks complete immediately (`aria-pressed`), tapping again undoes, failed save rolls back and announces "Could not save", control disabled while pending, no axe violations in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [ ] T010 [US1] Schemas `CheckInSet`, `CheckInState`, `CheckInList` in src/backend/app/schemas/check_ins.py
- [ ] T011 [US1] Services `editable_window`, `set_check_in` (upsert/delete), `list_for_date` in src/backend/app/services/check_ins.py
- [ ] T012 [US1] `PUT /api/v1/habits/{habit_id}/check-ins/{date}`, `GET /api/v1/check-ins` in src/backend/app/routers/check_ins.py and src/backend/app/main.py
- [ ] T013 [US1] Export OpenAPI and regenerate types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [ ] T014 [US1] Check-ins API + `useCheckIns(date)`, optimistic `useToggleCheckIn` in src/frontend/src/features/check-ins/
- [ ] T015 [US1] `CheckInButton` (`aria-pressed`, ✓ glyph) and Today list wiring in src/frontend/src/features/check-ins/components/CheckInButton.tsx and src/frontend/src/features/today/TodayPage.tsx

## Phase 4: User Story 2 - Backfill a Past Day (P2)

**Goal**: Navigate up to 30 days back and toggle completion there.

### Tests (write first)

- [ ] T016 [P] [US2] API tests: yesterday and today-30 accepted (FR-002); tomorrow and today-31 → 422 `DATE_OUT_OF_RANGE` (FR-003); window follows user tz in src/backend/tests/api/test_check_ins_api.py
- [ ] T017 [P] [US2] Component tests: Previous day shows yesterday's own state; Today returns; Next disabled on today; Previous disabled at today-30; `?date=` older than 30 days or in the future disables controls with explanation in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [ ] T018 [US2] `DayNav` (Previous / Today / Next, `?date=` search param) and disabled-state explanation in src/frontend/src/features/today/DayNav.tsx and src/frontend/src/features/today/TodayPage.tsx

## Phase 5: User Story 3 - Add a Note (P3)

### Tests (write first)

- [ ] T019 [P] [US3] API tests: note ≤ 280 saved and returned, trimmed, empty → null, 281 → 422, omitted note keeps existing (FR-005) in src/backend/tests/api/test_check_ins_api.py
- [ ] T020 [P] [US3] Component test: on a completed habit, "Add note" → type → Save shows the note in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [ ] T021 [US3] `NoteEditor` and `useSaveNote` in src/frontend/src/features/check-ins/

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Playwright @p1 journey: toggle today, reload, undo, backfill yesterday, keyboard toggle, axe in src/frontend/e2e/check-in.spec.ts
- [ ] T023 Mark spec Implemented in docs/specs/003-daily-check-in/spec.md and docs/specs/README.md
- [ ] T024 Run quickstart.md validation

## Dependencies & Execution Order

Foundational (T002–T007) → US1 → US2 → US3 → Polish. US2 and US3 reuse the US1 endpoint and
Today wiring, so they run after it.

## Implementation Strategy

MVP = US1. US2 (P2) and US3 (P3) ship in the same PR because they reuse the same endpoint and
the day navigation is needed by spec 006.
