# Implementation Plan: Today Dashboard

**Branch**: `006-today-dashboard` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/006-today-dashboard/spec.md`

## Summary

Turns the day view built in specs 003–005 into the home dashboard: `GET /days/{date}` gains
`due_count`, `completed_count`, and `habit_count`; the page shows "3 of 5 done" with a progress
bar and a polite live region, an empty state for users with no habits, an all-done state, a
"Done" section that completed habits move into, skeleton loading, and a date header that rolls
over at local midnight without a reload.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.9 strict

**Primary Dependencies**: Existing stack. No new dependencies.

**Storage**: No schema change

**Testing**: pytest API + perf (day summary p95 with 50 habits / 10k check-ins); Vitest + MSW
with fake timers for midnight rollover; Playwright @p1 journey with axe and keyboard-only pass

**Target Platform**: Developer laptop, evergreen browsers

**Project Type**: Web application

**Performance Goals**: Day summary < 150 ms p95 with 50 habits and 10k check-ins (SC-002);
FCP < 1.5 s (SC-001; initial bundle stays under the 150 kB gzip budget)

**Constraints**: Progress announced via `aria-live="polite"` (FR-006); skeletons, not spinners

**Scale/Scope**: ≤ 50 due habits per day

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | No open clarifications. |
| II. Vertical Slices | PASS | Counts API + dashboard UI + tests per story. |
| III. Test-First | PASS | Tests precede implementation in tasks.md. |
| IV. Simplicity | PASS | Counts derived in the existing day summary; one-minute interval for midnight rollover instead of timezone math. |
| V. Explicit Contracts | PASS | `contracts/days.openapi.yaml`; snapshot + types refreshed. |
| VI. Local-First | PASS | No external calls. |
| VII. Human-Accountable | PASS | Commits/PR cite `006` and FR ids. |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
docs/specs/006-today-dashboard/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/days.openapi.yaml
```

### Source Code

```text
src/backend/app/schemas/days.py, services/days.py   # counts
src/backend/tests/api/test_day_summary_api.py
src/backend/tests/perf/test_perf_day_summary.py

src/frontend/src/
├── features/today/
│   ├── TodayPage.tsx          # dashboard composition
│   ├── DayProgress.tsx        # "3 of 5 done", progressbar, live region
│   ├── use-local-today.ts     # rolls over at local midnight
│   └── TodayPage.test.tsx
├── features/check-ins/hooks/use-check-ins.ts   # optimistic counts
└── shared/ui/Skeleton.tsx
src/frontend/e2e/today.spec.ts
```

**Structure Decision**: Same web-app layout as earlier specs.

## Complexity Tracking

No violations and no new dependencies.
