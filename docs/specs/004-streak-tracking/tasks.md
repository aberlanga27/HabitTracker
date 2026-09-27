---
description: "Task list for spec 004 Streak Tracking"
---

# Tasks: Streak Tracking

**Input**: Design documents from `docs/specs/004-streak-tracking/`

**Prerequisites**: plan.md, spec.md (incl. Clarifications), research.md, data-model.md, contracts/streaks.openapi.yaml

**Tests**: Required (constitution Principle III). Tests are written first and must fail.

Stories: US1 Current streak, US2 Longest streak, US3 Streaks respect schedules.

## Phase 1: Setup

- [ ] T001 Confirm no new dependencies (plan.md) and branch `004-streak-tracking` is based on `main`

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 `StreakRead` schema and `HabitRead.streak` in src/backend/app/schemas/streaks.py and src/backend/app/schemas/habits.py
- [ ] T003 `Viewer` / `ViewerDep` (user id, timezone, local today) replacing `TodayDep` in src/backend/app/core/auth.py and the habits/days routers
- [ ] T004 [P] Frontend fakes default `streak` on habits in src/frontend/src/test/habits-backend.ts

## Phase 3: User Story 1 - See Current Streak (P1) 🎯 MVP

### Tests (write first)

- [ ] T005 [P] [US1] Unit tests: 3 consecutive days incl. today → 3; completed yesterday not today → count through yesterday; gap two days ago → only days after the gap; created today with one check-in → 1; undo recalculates; no check-ins → 0 in src/backend/tests/unit/test_streaks.py
- [ ] T006 [P] [US1] API tests: `streak` present on list/detail/mutations and `/days/{date}` items; values follow check-ins and undo within the same request cycle (FR-004, FR-005); today uses the user's timezone in src/backend/tests/api/test_streaks_api.py
- [ ] T007 [P] [US1] Component tests: Today row and habits list show "Current streak: 3 days" badge in src/frontend/src/features/streaks/StreakBadge.test.tsx and src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [ ] T008 [US1] Pure `compute_streak` (current part) in src/backend/app/services/streaks.py
- [ ] T009 [US1] `read_many` loads check-in dates once and fills `streak`; archived habits freeze at archive local date in src/backend/app/services/habits.py
- [ ] T010 [US1] Export OpenAPI and regenerate types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [ ] T011 [US1] `StreakBadge` on `CheckInRow` and `HabitRow` in src/frontend/src/features/streaks/ and src/frontend/src/features/{check-ins,habits}/components/

## Phase 4: User Story 2 - See Longest Streak (P2)

### Tests (write first)

- [ ] T012 [P] [US2] Unit tests: runs of 5 and 2 → longest 5 with start/end dates; ties keep the earliest; longest ≥ current in src/backend/tests/unit/test_streaks.py
- [ ] T013 [P] [US2] Component test: habit detail shows longest streak with its date range; unknown id shows not found in src/frontend/src/features/habits/components/HabitDetailPage.test.tsx

### Implementation

- [ ] T014 [US2] Longest-run tracking in src/backend/app/services/streaks.py
- [ ] T015 [US2] `useHabit(id)`, `HabitDetailPage`, `/habits/:id` route, name link in list in src/frontend/src/features/habits/ and src/frontend/src/app/routes.tsx

## Phase 5: User Story 3 - Streaks Respect Schedules (P2)

### Tests (write first)

- [ ] T016 [P] [US3] Unit tests: Mon/Wed/Fri completed Mon+Wed → 2 on Thu; Fri missed → 0 on Sat; unscheduled check-ins ignored; schedule change MWF→daily keeps the run (spec 005 US4); 3×/week met weeks chain and unmet past week breaks, open week never breaks; archived freeze; DST dates in src/backend/tests/unit/test_streaks.py
- [ ] T017 [P] [US3] API test: MWF habit streak over a week via backfilled check-ins in src/backend/tests/api/test_streaks_api.py

### Implementation

- [ ] T018 [US3] Schedule-aware walk (weekdays skip, times-per-week weeks) in src/backend/app/services/streaks.py

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T019 [P] SC-001 perf test: 2 years of daily check-ins < 20 ms (marker `perf`) in src/backend/tests/perf/test_perf_streaks.py
- [ ] T020 [P] Playwright @p1 journey: backfill two days + today → 🔥 3, undo today → 2, detail shows longest, axe in src/frontend/e2e/streaks.spec.ts
- [ ] T021 Mark spec Implemented in docs/specs/004-streak-tracking/spec.md and docs/specs/README.md
- [ ] T022 Run quickstart.md validation

## Dependencies & Execution Order

Foundational (T002–T004) → US1 → US2 → US3 → Polish; all stories extend `services/streaks.py`.

## Implementation Strategy

MVP = US1. US2 and US3 (P2) ship in the same PR since they extend the same pure function.
