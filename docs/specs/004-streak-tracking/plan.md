# Implementation Plan: Streak Tracking

**Branch**: `004-streak-tracking` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/004-streak-tracking/spec.md`

## Summary

A pure, schedule-aware `compute_streak` walks a habit's local dates once and returns the current
streak (ending today or the most recent scheduled day) and the longest streak with its date range.
It uses the schedule active on each date (spec 005 history), freezes at the archive date for
archived habits, and treats "today" as pending rather than missed. Every `HabitRead` (habit list,
habit detail, day summary) carries a `streak` object computed on read with one extra query for
the listed habits' check-in dates. The UI shows a flame + count on Today and the habits list and
adds a habit detail page with the longest streak.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.9 strict

**Primary Dependencies**: Existing stack. No new dependencies.

**Storage**: No schema change (derived data, ADR-3)

**Testing**: pytest unit-heavy (pure function incl. schedule history, DST dates, archive freeze,
2-year perf) + API exposure; Vitest + MSW; Playwright @p1 journey

**Target Platform**: Developer laptop, evergreen browsers

**Project Type**: Web application

**Performance Goals**: 2 years of daily check-ins < 20 ms per habit (SC-001)

**Constraints**: Local dates in the user's timezone; no background jobs (FR-004)

**Scale/Scope**: ≤ 50 habits × ~730 days each

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | Two ambiguities resolved in spec.md "Clarifications" (flagged for product review). |
| II. Vertical Slices | PASS | Streak API + flame UI + detail page + tests. |
| III. Test-First | PASS | Tests precede implementation in tasks.md. |
| IV. Simplicity | PASS | One pure function, no cache, no denormalized column. |
| V. Explicit Contracts | PASS | `contracts/streaks.openapi.yaml`; snapshot + types refreshed. |
| VI. Local-First | PASS | No external calls. |
| VII. Human-Accountable | PASS | Commits/PR cite `004` and FR ids. |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
docs/specs/004-streak-tracking/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/streaks.openapi.yaml
```

### Source Code

```text
src/backend/app/
├── services/streaks.py        # pure compute_streak
├── schemas/streaks.py         # StreakRead
├── schemas/habits.py          # HabitRead.streak
├── services/habits.py         # read_many loads check-in dates once
└── core/auth.py               # ViewerDep (user id, timezone, local today)
src/backend/tests/
├── unit/test_streaks.py
├── api/test_streaks_api.py
└── perf/test_perf_streaks.py

src/frontend/src/
├── features/streaks/          # StreakBadge
├── features/habits/components/HabitDetailPage.tsx   # /habits/:id
└── app/routes.tsx
src/frontend/e2e/streaks.spec.ts
```

**Structure Decision**: Same web-app layout as earlier specs.

## Complexity Tracking

No violations and no new dependencies.
