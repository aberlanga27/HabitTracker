---
description: "Task list for spec 002 Habit Management"
---

# Tasks: Habit Management

**Input**: Design documents from `docs/specs/002-habit-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/habits.openapi.yaml

**Tests**: Required (constitution Principle III). Tests are written first and must fail.

## Format: `[ID] [P?] [Story] Description`

Stories: US1 Create, US2 Edit, US3 Archive/Restore, US4 Delete, US5 Reorder.

## Phase 1: Setup

- [ ] T001 Confirm no new dependencies are needed (plan.md Complexity Tracking) and branch `002-habit-management` is based on `main`

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 `Habit` model (name 1–80, description ≤ 500 nullable, icon ≤ 16 nullable, color enum default `coral`, position, archived_at nullable, created_at; FK user ON DELETE CASCADE) in src/backend/app/models/habit.py
- [ ] T003 Migration `0003` creating `habit` with index `(user_id, archived_at)` in src/backend/app/migrations/versions/0003_habit.py
- [ ] T004 [P] `make_habit` factory in src/backend/tests/factories.py
- [ ] T005 [P] In-memory MSW habits backend for component tests in src/frontend/src/test/habits-backend.ts
- [ ] T006 [P] Habit query keys in src/frontend/src/shared/lib/queryKeys.ts

## Phase 3: User Story 1 - Create a Habit (P1) 🎯 MVP

**Goal**: Users add a habit that appears immediately and persists.

**Independent Test**: Create "Read 10 pages", confirm it is listed after reload.

### Tests (write first)

- [ ] T007 [P] [US1] Unit tests for schema rules: name trimmed and 1–80, description ≤ 500 and empty → null, icon rules (R2), color enum, default `coral` in src/backend/tests/unit/test_habit_schemas.py
- [ ] T008 [P] [US1] API tests: create → 201 appended at end (FR-001); blank/81-char name → 422; 50 active → 51st is 409 `HABIT_LIMIT_REACHED` with "Habit limit reached (50)" and archived habits do not count (FR-006); list scoped to owner, other user's id → 404 (FR-007) in src/backend/tests/api/test_habits_api.py
- [ ] T009 [P] [US1] Component tests: create form adds habit to list; blank or > 80 name shows inline error and sends nothing; limit error shown; emoji and color pickers are labelled radio groups; no axe violations in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [ ] T010 [US1] Schemas `HabitCreate`, `HabitUpdate`, `HabitRead`, `HabitList`, `HabitOrder` in src/backend/app/schemas/habits.py
- [ ] T011 [US1] Services `create`, `list_habits`, `get_owned` with 50-active limit and ownership in src/backend/app/services/habits.py
- [ ] T012 [US1] `GET/POST /api/v1/habits`, `GET /api/v1/habits/{habit_id}` in src/backend/app/routers/habits.py and register in src/backend/app/main.py
- [ ] T013 [US1] Export OpenAPI and regenerate types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [ ] T014 [P] [US1] Palette constants and `EmojiPicker`, `ColorPicker` in src/frontend/src/features/habits/palette.ts and src/frontend/src/shared/ui/
- [ ] T015 [US1] Habits API + hooks (`useHabits`, `useCreateHabit`) in src/frontend/src/features/habits/api.ts and src/frontend/src/features/habits/hooks/use-habits.ts
- [ ] T016 [US1] `HabitForm`, `HabitList`, `HabitsPage`, `/habits` route, header nav in src/frontend/src/features/habits/components/ and src/frontend/src/app/
- [ ] T017 [US1] Interim Today list of active habits with "Create your first habit" empty state in src/frontend/src/features/today/TodayPage.tsx

## Phase 4: User Story 2 - Edit a Habit (P1) 🎯 MVP

**Goal**: Users change name, description, icon, color without losing history.

### Tests (write first)

- [ ] T018 [P] [US2] API tests: PATCH updates provided fields only, null clears description/icon, validation errors 422, foreign id 404 (FR-002, FR-007) in src/backend/tests/api/test_habits_api.py
- [ ] T019 [P] [US2] Component tests: Edit → Save updates the row; Edit → Cancel sends nothing and keeps values in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [ ] T020 [US2] `update` service and `PATCH /api/v1/habits/{habit_id}` in src/backend/app/services/habits.py and src/backend/app/routers/habits.py
- [ ] T021 [US2] `useUpdateHabit` and inline edit mode in `HabitRow` in src/frontend/src/features/habits/

Note: "rename keeps check-ins" (SC-002) is asserted in spec 003's tests once check-ins exist.

## Phase 5: User Story 3 - Archive and Restore (P2)

### Tests (write first)

- [ ] T022 [P] [US3] API tests: archive sets `archived_at`, leaves active list, appears with `archived=true`; restore clears it and appends; both idempotent; restore at 50 active → 409 (FR-003, FR-006) in src/backend/tests/api/test_habits_api.py
- [ ] T023 [P] [US3] Component tests: Archive moves habit to "Archived" section and off Today; Restore brings it back in src/frontend/src/features/habits/components/HabitsPage.test.tsx and src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [ ] T024 [US3] `archive`/`restore` services and `POST .../archive`, `POST .../restore` in src/backend/app/services/habits.py and src/backend/app/routers/habits.py
- [ ] T025 [US3] `useArchiveHabit`, `useRestoreHabit`, `ArchivedList` in src/frontend/src/features/habits/

## Phase 6: User Story 4 - Delete a Habit (P3)

### Tests (write first)

- [ ] T026 [P] [US4] API tests: DELETE → 204 and subsequent GET 404; foreign id 404 (FR-004, FR-007) in src/backend/tests/api/test_habits_api.py
- [ ] T027 [P] [US4] Component tests: Delete stays disabled until the exact name is typed; confirm removes; Cancel removes nothing in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [ ] T028 [US4] `delete` service and `DELETE /api/v1/habits/{habit_id}` in src/backend/app/services/habits.py and src/backend/app/routers/habits.py
- [ ] T029 [US4] `useDeleteHabit` and `DeleteHabitConfirm` in src/frontend/src/features/habits/

## Phase 7: User Story 5 - Reorder Habits (P3)

### Tests (write first)

- [ ] T030 [P] [US5] API tests: PUT order rewrites positions and persists; missing/extra/foreign/archived ids → 422 (FR-005, FR-007) in src/backend/tests/api/test_habits_api.py
- [ ] T031 [P] [US5] Component tests: "Move up"/"Move down" reorder via keyboard; first row has no enabled "Move up" in src/frontend/src/features/habits/components/HabitsPage.test.tsx

### Implementation

- [ ] T032 [US5] `reorder` service and `PUT /api/v1/habits/order` in src/backend/app/services/habits.py and src/backend/app/routers/habits.py
- [ ] T033 [US5] `useReorderHabits` and move buttons in `HabitRow` in src/frontend/src/features/habits/

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T034 [P] SC-003: component timing test rendering 50 habits < 100 ms in src/frontend/src/features/habits/components/HabitList.test.tsx
- [ ] T035 [P] Playwright @p1 journey: create, reload, edit, archive/restore, reorder by keyboard, delete, with axe in src/frontend/e2e/habits.spec.ts
- [ ] T036 Mark spec Implemented in docs/specs/002-habit-management/spec.md and docs/specs/README.md
- [ ] T037 Run quickstart.md validation

## Dependencies & Execution Order

- Foundational (T002–T006) blocks all stories. US1 → US2 → US3 → US4 → US5 share
  `services/habits.py`, `routers/habits.py`, and `HabitRow`, so they run sequentially; test
  tasks within a story are parallel.

## Implementation Strategy

MVP = US1 + US2. US3–US5 are small and ship in the same PR so the habit list is complete before
schedules (005) and check-ins (003) build on it.
