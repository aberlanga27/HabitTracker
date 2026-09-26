# Implementation Plan: Daily Check-In

**Branch**: `003-daily-check-in` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/003-daily-check-in/spec.md`

## Summary

One-tap toggle of a habit's completion for a local date, idempotent on the server
(`PUT /habits/{id}/check-ins/{date}`), restricted to today and the previous 30 days in the
user's stored timezone, at most one check-in per habit per date, optional ≤ 280-char note. The
Today page gains optimistic toggles with rollback, previous/next/today navigation over the
30-day window, and a note editor. Spec 006 later swaps the data source for the day summary.

## Technical Context

**Language/Version**: Python 3.13; TypeScript 5.9 strict

**Primary Dependencies**: Existing stack. No new dependencies.

**Storage**: SQLite; new `check_in` table (migration `0004`) with `UNIQUE(habit_id, local_date)`

**Testing**: pytest unit (date window) + API; Vitest + MSW (optimistic update, rollback,
disabled states); Playwright @p1 journey

**Target Platform**: Developer laptop, evergreen browsers

**Project Type**: Web application

**Performance Goals**: Visual feedback < 100 ms via optimistic update (SC-001); endpoints
< 200 ms p95

**Constraints**: Server computes "today" from the injected clock and the user's timezone
(FR-007, ADR-4); duplicate-safe under rapid taps (SC-002)

**Scale/Scope**: ≤ 50 habits × 31 editable days per user

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | No open clarifications. |
| II. Vertical Slices | PASS | Toggle, backfill, and note each ship API + UI + tests. |
| III. Test-First | PASS | Tests precede implementation in tasks.md. |
| IV. Simplicity | PASS | Upsert via SQLite `ON CONFLICT DO NOTHING`; no queue for offline taps (spec Assumptions). |
| V. Explicit Contracts | PASS | `contracts/check-ins.openapi.yaml`; snapshot + generated types refreshed. |
| VI. Local-First | PASS | No external calls. |
| VII. Human-Accountable | PASS | Commits/PR cite `003` and FR ids. |

Post-design re-check: PASS.

## Project Structure

### Documentation (this feature)

```text
docs/specs/003-daily-check-in/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/check-ins.openapi.yaml
```

### Source Code

```text
src/backend/app/
├── models/check_in.py
├── schemas/check_ins.py
├── services/check_ins.py        # date window, toggle, list by date
├── routers/check_ins.py
└── migrations/versions/0004_check_in.py
src/backend/tests/
├── unit/test_check_in_window.py
└── api/test_check_ins_api.py

src/frontend/src/
├── shared/lib/dates.ts          # localToday(tz, now), addDays, formatDayLabel
├── features/check-ins/          # api.ts, types.ts, hooks/use-check-ins.ts,
│                                # components/CheckInButton.tsx, NoteEditor.tsx
├── features/today/              # TodayPage with day navigation + toggles
└── test/check-ins-backend.ts    # in-memory MSW check-ins API
src/frontend/e2e/check-in.spec.ts
```

**Structure Decision**: Same web-app layout as specs 001–002.

## Complexity Tracking

No violations and no new dependencies.
