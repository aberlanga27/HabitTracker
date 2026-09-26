# Testing Guide

This document defines how Habitude is tested. It applies to humans and AI agents
alike and is governed by Principle III of `.specify/memory/constitution.md`
(Test-First, NON-NEGOTIABLE). Commands in section 13 are live; sections marked *planned*
(xdist, CI) arrive with their own specs.

## 1. Philosophy: Spec-Driven Tests

- Tests are written **before** implementation, derived from the feature spec in
  `docs/specs/NNN-name/spec.md`. Red → Green → Refactor.
- **Every functional requirement (FR-xxx) maps to at least one automated test.**
  A reviewer must be able to grep a spec ID and find its tests.
- **Acceptance scenarios become test names.** The Given/When/Then wording in the
  spec is preserved in the test name or `describe`/`it` text so failures read like
  the spec.
- Success criteria (SC-xxx) that are measurable on a laptop (latency, render time,
  duplicate counts) are also tests, tagged `perf` and run in CI nightly plus on demand.
- A behavior without a test does not exist. A PR with untested behavior is not mergeable.

## 2. Test Pyramid and Target Ratios

| Layer | Tool | Scope | Target share | Speed budget |
|---|---|---|---|---|
| Backend unit | pytest | Pure functions: streak math, schedule "is due", date/timezone helpers, validators | ~50% | < 5 ms each |
| Backend API / integration | pytest + httpx `AsyncClient` + throwaway SQLite per test | Route → service → DB, auth, contracts | ~30% | < 100 ms each |
| Frontend component | Vitest + Testing Library + MSW | Components, hooks, query logic, a11y roles | ~15% | < 50 ms each |
| End-to-end | Playwright | **P1 user journeys only**, one happy path + one failure path per P1 story | ~5% | < 30 s each |

Rules of thumb: if a bug can be reproduced one layer lower, write the test there.
E2E is for proving the slice works together, not for exhaustive edge cases.

## 3. Tooling per Layer

### Backend (`src/backend/`)
- `pytest`, `pytest-asyncio` (async routes), `pytest-cov` (coverage), `hypothesis` optional for date property tests.
- `httpx.AsyncClient(app=app, base_url="http://test")` against the FastAPI app; no live server.
- One **fresh SQLite database per test** (`sqlite:///:memory:` or a `tmp_path` file), schema created via the Alembic head so migrations are exercised.
- **Factories**: small helpers in `tests/factories.py` (`make_user()`, `make_habit()`, `make_checkin()`), no ORM-model fixtures shared across tests.
- **Clock**: all time reads go through a `Clock` provider injected into services; tests supply `FrozenClock(datetime(...), tz=...)`. `freezegun` is acceptable for legacy spots, but the provider is preferred so streak/reminder logic is deterministic and timezone-aware.

### Frontend (`src/frontend/`)
- `vitest` with `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`.
- `msw` (Mock Service Worker) to mock the REST API at the network boundary; components are never given fake props to bypass fetching.
- `vi.useFakeTimers()` / `vi.setSystemTime()` for reminder and midnight-rollover tests.
- Playwright (`@playwright/test`) with `@axe-core/playwright` for e2e and accessibility.

## 4. Layout and Naming Conventions

```
src/backend/tests/
  conftest.py          # app, client, db, clock fixtures (function-scoped)
  factories.py         # make_user / make_habit / make_checkin
  unit/                # test_streaks.py, test_schedules.py, test_dates.py ...
  api/                 # test_auth_api.py, test_habits_api.py, test_checkins_api.py ...
  perf/                # test_perf_budgets.py (marker: perf)
src/frontend/src/**/Component.test.tsx   # colocated with the component
src/frontend/e2e/                        # *.spec.ts Playwright journeys
```

**Naming from spec IDs**

- pytest: `test_fr003_rejects_future_dates`, `test_us1_s2_tap_completed_habit_undoes_it`.
  Prefix with the spec number when a file covers several specs: `test_s003_fr004_one_checkin_per_habit_per_date`.
- Vitest / Playwright: `describe("spec 003 US1 - Check in for today")` and
  `it("given an uncompleted habit, when tapped, then it is marked complete within 100ms")`.
- Files are named by feature, not by layer: `test_checkins_api.py`, `TodayView.test.tsx`, `check-in.spec.ts`.
- Markers: `@pytest.mark.perf`, `@pytest.mark.slow`; Playwright tags `@p1`, `@a11y`.

## 5. Fixtures and Test Data Rules

- **No shared mutable fixtures.** Everything is function-scoped; module/session scope only for immutable config.
- **Deterministic dates.** Never call `datetime.now()` / `new Date()` in a test. Use the injected clock or fake timers.
- **Timezone-aware cases are mandatory** for any date logic:
  - a check-in at **23:59 local** counts for that local date, not the UTC date;
  - a **DST boundary** (e.g. `America/Mexico_City` or `Europe/Madrid` spring-forward) does not create or skip a day;
  - user timezone differs from server timezone (server runs as UTC in tests).
- Seeded data is built via factories inside the test; no JSON fixture dumps except for the export/import spec (011).
- Tests must pass in any order and in parallel (`pytest -p xdist` planned).

## 6. What to Mock, What Not To

| Mock | Never mock |
|---|---|
| The clock / system time | The database in API tests (use a real throwaway SQLite) |
| Browser `Notification` API and permission state | FastAPI dependency wiring (test through the app) |
| Network in frontend component tests (MSW) | Pydantic validation / SQLModel constraints |
| `window.matchMedia` for theme tests | Streak/schedule logic when testing the dashboard (use real functions with seeded data) |

## 7. Coverage Thresholds and Enforcement

- Backend: **≥ 85% line coverage on changed modules** (constitution gate), 80% project floor.
  Enforced with `pytest --cov=app --cov-fail-under=80` plus a diff-coverage check on PRs.
- Frontend: 80% statements on `src/frontend/src`, enforced in `vitest.config.ts` `coverage.thresholds`.
- E2E has no coverage number; every P1 story must have at least one `@p1` journey.
- Coverage never justifies a test without an assertion. Reviewers reject "coverage-only" tests.

## 8. Spec-to-Test Map

| Spec | Primary test types | Tricky cases to cover |
|---|---|---|
| 001 User Accounts | API (register/login/logout/session), unit (password rules) | Case-insensitive email, lockout after 5 fails/15 min, 30-day expiry, generic error text, no plaintext in logs |
| 002 Habit Management | API CRUD, component (form validation), e2e create | 50-habit cap, rename keeps check-ins, archive freezes streak, typed delete confirmation, keyboard reorder |
| 003 Daily Check-In | API, unit (date window), component (optimistic UI), e2e | 20 rapid taps → 1 row, future/ >30-day rejection, 23:59 local, rollback on failure |
| 004 Streak Tracking | Unit heavy (property-based), API for exposure | Gap resets, "yesterday still counts", schedule-aware skips, DST, archived freeze, 2-year dataset < 20 ms |
| 005 Habit Schedules | Unit ("is due"), API (validation) | 7x/week → daily, empty weekday set rejected, schedule history for past streaks, Monday week start |
| 006 Today Dashboard | Component, e2e (P1), API for day summary | Empty / all-done states, 30-day navigation bounds, midnight rollover with fake timers, skeleton loading |
| 007 History Calendar | API (366-day range), component (rendering, tooltips) | Not-due vs 0%, pre-creation neutral cells, focusable cells with a11y names, contrast per shade in both themes |
| 008 Reminders | Component with fake timers, unit (batching) | Fires only if due and incomplete, same-minute batching, permission denied fallback, archived habits silent |
| 009 Stats & Insights | Unit (aggregations), API | Division by zero on empty ranges, partial weeks, timezone week boundaries |
| 010 Categories & Tags | API, component (filtering) | Deleting a category unassigns not deletes habits, filter persistence, multi-tag habits |
| 011 Data Export & Import | API (file round trip), unit (schema validation) | Export → import produces identical data, malformed file rejected, duplicate-safe re-import |
| 012 Settings & Preferences | API, component (theme), e2e (timezone change) | Timezone change shifts "today" correctly, week-start affects heatmap, prefers-color-scheme fallback |

## 9. Accessibility Testing

- Every Playwright journey runs `AxeBuilder` after each page settles; any WCAG 2.1 AA violation fails the run.
- One **keyboard-only** e2e per P1 story: navigate, check in, reorder, sign out without a pointer.
- Component tests query by role and accessible name (`getByRole`), never by test IDs unless no semantic handle exists.
- Progress changes on the dashboard are asserted via `aria-live` region content.

## 10. Performance Budgets as Tests

Seed a user with 50 habits and **10 000 check-ins** in `tests/perf/`, then assert:

| Budget (from constitution / specs) | Test |
|---|---|
| Any API endpoint < 200 ms p95 | `test_perf_all_endpoints_p95` over 50 requests each |
| Day summary < 150 ms p95 | `test_perf_day_summary_p95` |
| Streak over 2 years of daily data < 20 ms | `test_perf_streak_two_years` |
| 366-day calendar range < 200 ms p95 | `test_perf_calendar_range_p95` |
| Heatmap 366 cells render < 50 ms | Vitest timing test, marked `perf` |

Perf tests are marked `perf`, skipped by default, and run nightly and on `perf` label.

## 11. CI Gates (planned `.github/workflows/ci.yml`)

Specified in [docs/specs/013-pr-analysis-pipeline/spec.md](specs/013-pr-analysis-pipeline/spec.md).

1. `ruff check` and `ruff format --check`
2. `mypy --strict src/backend`
3. `pytest --cov --cov-fail-under=80` + diff coverage ≥ 85% on changed modules
4. `npm run lint` and `tsc --noEmit`
5. `vitest run --coverage` with thresholds
6. `playwright test --grep @p1` including axe checks
7. PR description references a spec ID (`docs/specs/NNN-...`) — enforced by a lightweight check

## 12. Examples

**pytest, spec 003 FR-003 / FR-004**

```python
# src/backend/tests/api/test_checkins_api.py  (planned)
import pytest
from datetime import date

@pytest.mark.asyncio
async def test_fr003_rejects_future_dates(client, user, habit, clock):
    clock.set(date(2026, 9, 26), tz="America/Mexico_City")
    resp = await client.post(f"/habits/{habit.id}/checkins", json={"date": "2026-09-27"})
    assert resp.status_code == 422
    assert "future" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_s003_fr004_one_checkin_per_habit_per_date(client, habit, db):
    for _ in range(20):  # rapid-fire taps must not duplicate
        await client.put(f"/habits/{habit.id}/checkins/2026-09-26", json={"completed": True})
    assert db.count_checkins(habit.id, date(2026, 9, 26)) == 1
```

**Vitest, spec 003 US1**

```tsx
// src/frontend/src/features/today/HabitRow.test.tsx  (planned)
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server, http, HttpResponse } from "@/test/msw";

describe("spec 003 US1 - Check in for today", () => {
  it("given an uncompleted habit, when tapped, then it is marked complete optimistically", async () => {
    render(<HabitRow habit={{ id: 1, name: "Read 10 pages", completed: false }} />);
    await userEvent.click(screen.getByRole("checkbox", { name: /read 10 pages/i }));
    expect(screen.getByRole("checkbox", { name: /read 10 pages/i })).toBeChecked();
  });

  it("given a failing save, when tapped, then the UI rolls back and shows an error", async () => {
    server.use(http.put("/api/habits/1/checkins/:date", () => HttpResponse.error()));
    render(<HabitRow habit={{ id: 1, name: "Read 10 pages", completed: false }} />);
    await userEvent.click(screen.getByRole("checkbox", { name: /read 10 pages/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/could not save/i);
    expect(screen.getByRole("checkbox", { name: /read 10 pages/i })).not.toBeChecked();
  });
});
```

## 13. Commands

```bash
# backend (from src/backend; coverage gate is configured in pyproject.toml)
../../.venv/bin/pytest                                # unit + api + contract with coverage
../../.venv/bin/pytest -m perf                        # performance budgets
../../.venv/bin/pytest tests/api/test_auth_login_api.py -k fr007 --no-cov   # one FR

# frontend (from src/frontend)
npm test                                              # vitest
npm run test:coverage                                 # vitest with 80% statement threshold
npm run test:e2e                                      # playwright @p1 + axe (starts both servers)
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e            # use an installed Chrome
```

Test harness notes: backend tests copy an Alembic-migrated template SQLite file per test
(`tests/conftest.py`) and use `FrozenClock` from `tests/fakes.py`; component tests render the
real route tree with `renderApp()` from `src/test/render.tsx` and mock the API with MSW.

Related: `docs/coding-standards.md`, `docs/frontend.md`, `docs/specs/README.md`.
