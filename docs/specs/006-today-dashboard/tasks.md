---
description: "Task list for spec 006 Today Dashboard"
---

# Tasks: Today Dashboard

**Input**: Design documents from `docs/specs/006-today-dashboard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/days.openapi.yaml

**Tests**: Required (constitution Principle III). Tests are written first and must fail.

Stories: US1 See today at a glance, US2 Navigate between days, US3 Group by completion.

## Phase 1: Setup

- [X] T001 Confirm no new dependencies (plan.md) and branch `006-today-dashboard` is based on `main`

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 [P] `Skeleton` component in src/frontend/src/shared/ui/Skeleton.tsx and src/frontend/src/shared/ui/index.ts
- [X] T003 [P] Day fake returns counts in src/frontend/src/test/day-backend.ts and src/frontend/src/test/server.ts

## Phase 3: User Story 1 - See Today at a Glance (P1) 🎯 MVP

### Tests (write first)

- [X] T004 [P] [US1] API tests: `due_count`, `completed_count`, `habit_count`; done-for-week not counted; archived excluded; zero habits → all zero (FR-001, FR-002, FR-005) in src/backend/tests/api/test_day_summary_api.py
- [X] T005 [P] [US1] Component tests: 5 due / 3 done → "3 of 5 habits done", progressbar 60, live region polite; zero habits → CTA; all done → "All done for today"; loading shows skeleton with `aria-busy`; toggling updates the live region optimistically; axe clean in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [X] T006 [US1] Counts in `DaySummary` and `day_summary` in src/backend/app/schemas/days.py and src/backend/app/services/days.py
- [X] T007 [US1] Export OpenAPI and regenerate types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [X] T008 [US1] `DayProgress` and dashboard states in src/frontend/src/features/today/DayProgress.tsx and src/frontend/src/features/today/TodayPage.tsx
- [X] T009 [US1] Optimistic `completed_count` in src/frontend/src/features/check-ins/hooks/use-check-ins.ts

## Phase 4: User Story 2 - Navigate Between Days (P2)

### Tests (write first)

- [X] T010 [P] [US2] Component tests: header rolls over at local midnight with fake timers when viewing today; explicit `?date=` does not move in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [X] T011 [US2] `useLocalToday(timezone)` in src/frontend/src/features/today/use-local-today.ts

(Previous/Next/Jump-to-today navigation and 30-day bounds shipped with spec 003 US2 and remain covered by its tests.)

## Phase 5: User Story 3 - Group by Completion (P3)

### Tests (write first)

- [X] T012 [P] [US3] Component test: completing a due habit moves it from "To do" to "Done" without reload in src/frontend/src/features/today/TodayPage.test.tsx

### Implementation

- [X] T013 [US3] To do / Done sections in src/frontend/src/features/today/TodayPage.tsx (the fade-in was dropped: axe flagged mid-animation contrast; the move itself is immediate, inside the 300 ms budget)

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T014 [P] SC-002 perf test: `/days/{date}` p95 < 150 ms with 50 habits and 10k check-ins (marker `perf`) in src/backend/tests/perf/test_perf_day_summary.py
- [X] T015 [P] Playwright @p1 journey: empty state → create habits → progress → all done, keyboard-only toggling, axe in src/frontend/e2e/today.spec.ts
- [X] T016 Mark spec Implemented in docs/specs/006-today-dashboard/spec.md and docs/specs/README.md; update README status
- [X] T017 Run quickstart.md validation

## Dependencies & Execution Order

Foundational (T002–T003) → US1 → US2 → US3 → Polish; all stories touch `TodayPage.tsx`.

## Implementation Strategy

MVP = US1. US2 and US3 are small and complete the MVP tier in the same PR.
