# Implementation Plan: Habit Management

**Branch**: `002-habit-management` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/002-habit-management/spec.md`

## Summary

Signed-in users create, edit, archive/restore, permanently delete, and reorder their habits.
A habit has a name (1–80 chars, trimmed), optional description (≤ 500), optional emoji icon, and
one of eight palette colors. At most 50 active habits per user. Every query is scoped to the
current user; another user's habit is a `404`. The UI adds an "All habits" page (`/habits`) and
an interim Today list of active habits that spec 006 will replace with the day summary.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.9 strict

**Primary Dependencies**: Existing stack from spec 001 (FastAPI, SQLModel, Alembic; React 19,
TanStack Query, React Router). No new dependencies.

**Storage**: SQLite; new `habit` table via Alembic migration `0003`

**Testing**: pytest API + unit tests; Vitest + MSW component tests; Playwright @p1 journey

**Target Platform**: Developer laptop, evergreen browsers

**Project Type**: Web application

**Performance Goals**: List of 50 habits renders < 100 ms after data arrives (SC-003); list
endpoint < 200 ms p95

**Constraints**: Ownership on every query (FR-007); keyboard-operable reorder (FR-005)

**Scale/Scope**: ≤ 50 active habits per user, unbounded archived habits

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | No open clarifications in spec.md. |
| II. Vertical Slices | PASS | Each story ships endpoint + UI + tests. |
| III. Test-First | PASS | Tests precede implementation in tasks.md. |
| IV. Simplicity | PASS | No drag-and-drop library; move up/down buttons satisfy FR-005 for pointer and keyboard. |
| V. Explicit Contracts | PASS | `contracts/habits.openapi.yaml`; snapshot + generated types refreshed. |
| VI. Local-First | PASS | No external calls. |
| VII. Human-Accountable | PASS | Commits/PR cite `002` and FR ids. |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
docs/specs/002-habit-management/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/habits.openapi.yaml
```

### Source Code

```text
src/backend/app/
├── models/habit.py
├── schemas/habits.py
├── services/habits.py
├── routers/habits.py
└── migrations/versions/0003_habit.py
src/backend/tests/
├── unit/test_habit_schemas.py
└── api/test_habits_api.py

src/frontend/src/
├── features/habits/        # api.ts, types.ts, palette.ts, hooks/use-habits.ts,
│                           # components/ (HabitForm, HabitList, HabitRow, ArchivedList,
│                           #   DeleteHabitConfirm, HabitsPage)
├── features/today/TodayPage.tsx   # interim: active habits + empty-state CTA
├── shared/ui/EmojiPicker.tsx, ColorPicker.tsx
└── test/habits-backend.ts  # in-memory MSW habits API for component tests
src/frontend/e2e/habits.spec.ts
```

**Structure Decision**: Same web-app layout as spec 001.

## Complexity Tracking

No violations and no new dependencies.
