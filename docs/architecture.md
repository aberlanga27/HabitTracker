# Architecture

**Audience**: humans and AI agents planning or implementing Habitude features.
**Status**: planning document. Describes the target system; no application code exists yet. Specs live in `docs/specs/`, the constitution in `.specify/memory/constitution.md`.

## System Overview

```
┌──────────────────────────┐        HTTPS/JSON        ┌──────────────────────────┐        ┌───────────────┐
│  Browser                 │  ───────────────────▶    │  FastAPI (Python 3.13)   │  ───▶  │  SQLite file  │
│  React 19 SPA (Vite)     │  ◀───────────────────    │  SQLModel + Alembic      │  ◀───  │  habitude.db  │
│  TanStack Query cache    │   session cookie          │  /api/v1/*               │        └───────────────┘
│  localhost:5173          │                            │  localhost:8000          │
└──────────────────────────┘                            └──────────────────────────┘
        │ browser Notification API (reminders, spec 008)
        ▼
   OS notification
```

Single process, single database file, no external services. Everything runs on a developer laptop (constitution principle VI).

## Repository Layout

```
AE-CapstoneDemo/
├── AGENTS.md                 # instructions for AI coding agents (Copilot reads via .github/copilot-instructions.md)
├── README.md
├── requirements-tooling.txt  # specify-cli for the .venv
├── .venv/                    # Python virtualenv: specify-cli + backend tooling (git-ignored)
├── .specify/                 # Spec Kit: constitution, templates, scripts, workflows
│   └── memory/constitution.md
├── .github/
│   ├── copilot-instructions.md
│   ├── agents/               # custom Copilot agents
│   ├── prompts/              # reusable prompt files
│   ├── skills/speckit-*/     # Spec Kit slash commands
│   └── workflows/            # CI
├── docs/
│   ├── architecture.md       # this file
│   ├── frontend.md
│   ├── testing.md
│   ├── coding-standards.md
│   └── specs/                # one folder per feature: spec.md, plan.md, tasks.md, contracts/
│       ├── 001-user-accounts/
│       └── ...
└── src/
    ├── backend/
    └── frontend/
```

## Backend Layout (`src/backend/`)

```
src/backend/
├── pyproject.toml            # fastapi, sqlmodel, alembic, uvicorn; dev: pytest, ruff, mypy, httpx
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── main.py               # create_app(): routers, middleware, exception handlers
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings): DATABASE_URL, SESSION_TTL_DAYS, ...
│   │   ├── security.py       # password hashing (argon2), session token generation
│   │   ├── auth.py           # get_current_user dependency, login lockout
│   │   └── db.py             # engine, session factory, get_session dependency
│   ├── models/               # SQLModel tables: user.py, session.py, habit.py, schedule.py,
│   │                         #   check_in.py, reminder.py, category.py
│   ├── schemas/              # request/response models per feature (never expose table models directly)
│   ├── services/             # business logic, pure where possible:
│   │   ├── habits.py         #   spec 002
│   │   ├── check_ins.py      #   spec 003
│   │   ├── streaks.py        #   spec 004 (pure functions over date lists + schedules)
│   │   ├── schedules.py      #   spec 005 (is_due(habit, local_date))
│   │   ├── day_summary.py    #   spec 006
│   │   ├── heatmap.py        #   spec 007
│   │   ├── stats.py          #   spec 009
│   │   ├── export.py         #   spec 011
│   │   └── dates.py          #   timezone helpers
│   └── api/
│       ├── deps.py
│       └── v1/
│           ├── router.py     # includes all feature routers under /api/v1
│           ├── auth.py       # /auth/register, /auth/login, /auth/logout, /auth/me
│           ├── habits.py     # /habits, /habits/{id}, /habits/{id}/archive, /habits/reorder
│           ├── check_ins.py  # /habits/{id}/check-ins/{date}
│           ├── days.py       # /days/{date}
│           ├── heatmap.py    # /heatmap?habit=all|{id}&from&to
│           ├── reminders.py  # /habits/{id}/reminder
│           ├── stats.py      # /stats?range=
│           ├── categories.py # /categories
│           ├── export.py     # /export?format=csv|json
│           └── settings.py   # /me/settings
└── tests/
    ├── conftest.py           # in-memory SQLite, TestClient, factories, frozen clock
    ├── unit/                 # services (streaks, schedules, dates)
    ├── api/                  # one file per router, driven by spec acceptance scenarios
    └── contract/             # OpenAPI snapshot test
```

Layering rule: `api` → `services` → `models`. Routers parse and validate, services decide, models persist. Services never import from `api`.

## Request Lifecycle

1. Browser sends `fetch('/api/v1/days/2026-09-26', { credentials: 'include' })`.
2. Session middleware reads the `habitude_session` cookie, loads the `Session` row, rejects if missing or expired, else attaches `current_user` and bumps `last_used_at`.
3. Router validates path and body with a `schemas` model.
4. Router calls a service function with the user, a DB session, and validated inputs.
5. Service computes the result (queries, derived data) and returns plain schema objects.
6. Router returns JSON. Errors raised as `AppError(code, status, message, details)` are converted by a global handler to the error envelope below.
7. Frontend `apiClient` parses the response; TanStack Query caches it under the feature's query key.

## Authentication Model (spec 001)

- Email + password; passwords hashed with argon2id, never logged.
- On login the server creates a `Session` row with a random 256-bit opaque token and sets it in an `httpOnly`, `SameSite=Lax`, `Secure` (in production) cookie named `habitude_session`.
- Every authenticated request updates `last_used_at`. Sessions expire after 30 days of inactivity; expired sessions are rejected and deleted lazily.
- Logout deletes the `Session` row and clears the cookie.
- Lockout: 5 failed attempts per email within 15 minutes blocks login for 15 minutes (tracked in a small `login_attempt` table or in-memory for v1).
- Generic error messages on registration and login failures (spec 001 FR-008).

## Data Model

```
User
 ├── id (uuid), email (unique, case-insensitive), password_hash
 ├── timezone (IANA, e.g. "America/Monterrey"), week_start (mon|sun), theme
 └── created_at (UTC)
   │
   ├──< Session        id, token_hash, created_at, last_used_at, expires_at
   │
   ├──< Category       id, name, color, position                      (spec 010)
   │
   └──< Habit          id, name, description, icon, color, position,
         │             category_id (nullable → Category), archived_at (nullable), created_at
         │
         ├──< Schedule id, type (daily|weekdays|times_per_week), weekdays (bitmask),
         │             target_per_week, effective_from (local date)   (spec 005; history kept)
         │
         ├──< CheckIn  id, local_date (YYYY-MM-DD), completed_at (UTC), note
         │             UNIQUE(habit_id, local_date)                    (spec 003)
         │
         └──1 Reminder id, time_local (HH:MM), enabled                (spec 008)
```

Relations: `User 1—N Habit`, `Habit 1—N Schedule` (only the latest by `effective_from` is active), `Habit 1—N CheckIn`, `Habit 1—0..1 Reminder`, `Category 1—N Habit` (optional). Deleting a Habit cascades to its Schedules, CheckIns, and Reminder (spec 002).

Derived data (streaks, day summaries, heatmaps, stats) is **not stored**.

## Timezone Strategy

- All timestamps (`created_at`, `completed_at`, `last_used_at`) are stored in UTC.
- Each `User` stores an IANA timezone, captured at registration from the browser and editable in settings (spec 012).
- A check-in's `local_date` is the calendar date in the user's timezone at the moment of the request; the server computes it, the client only sends the date it is displaying.
- "Today", "is due", streaks, week boundaries, and reminder times are all evaluated by the server against the user's timezone via `services/dates.py` (`zoneinfo`).
- Changing timezone does not rewrite stored `local_date` values; it only affects evaluation going forward.

## Derived Data Is Computed on Read

| Derived value | Spec | Inputs | Where |
|---|---|---|---|
| `is_due(habit, date)` | 005 | active schedule for that date | `services/schedules.py` |
| Current / longest streak | 004 | check-in dates + schedule history + tz | `services/streaks.py` (pure) |
| Day summary | 006 | habits due on date + check-ins for date | `services/day_summary.py` |
| Heatmap statuses | 007 | up to 366 days of check-ins + schedules | `services/heatmap.py` |
| Completion rate, best day, trends | 009 | check-ins in range | `services/stats.py` |

Each is a function of the rows for one user, computed per request with at most a couple of indexed queries (`check_in(habit_id, local_date)`, `habit(user_id, archived_at)`). Budgets: streak over two years of data < 20 ms, 366-day heatmap < 200 ms p95 with 10k check-ins. If a budget is missed, the plan for that feature may introduce a per-user cache, but never a denormalized column without a spec amendment.

## API Conventions

- REST over JSON, all routes under `/api/v1`. OpenAPI served at `/api/v1/openapi.json` and is the contract the frontend generates types from (constitution principle V).
- Resource naming: plural nouns, kebab-case paths, `{id}` path params as UUID strings, dates as `YYYY-MM-DD`.
- Verbs: `GET` read, `POST` create or action (`/habits/{id}/archive`), `PATCH` partial update, `PUT` idempotent set (`/habits/{id}/check-ins/{date}`), `DELETE` remove.
- Success codes: `200` read/update, `201` create, `204` delete.
- Error envelope, always:

```json
{ "error": { "code": "HABIT_LIMIT_REACHED", "message": "Habit limit reached (50)", "details": { "limit": 50 } } }
```

  Common codes: `UNAUTHENTICATED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404), `VALIDATION_ERROR` (422, `details.fields`), `CONFLICT` (409), `LOCKED_OUT` (429).
- Ownership: every query is scoped by `user_id`; a habit belonging to another user is a `404`, never a `403`, to avoid enumeration.
- No pagination in v1: a user has at most 50 active habits and ranges are capped at 366 days.
- Breaking changes require a new spec and a note in `docs/specs/README.md`.

## Local Development Ports

| Service | Port | Command *(planned)* |
|---|---|---|
| Backend (uvicorn, reload) | 8000 | `.venv/bin/uvicorn app.main:app --reload` from `src/backend/` |
| Frontend (Vite) | 5173 | `npm run dev` from `src/frontend/` |

Vite proxies `/api` to `http://localhost:8000` so the session cookie is first-party in development.

## Decisions Log

| # | Decision | Rationale | Date |
|---|---|---|---|
| ADR-1 | SQLite as the only database | Local-first, zero setup, sufficient for one user with 10k check-ins; SQLModel keeps a path to Postgres if sync ever arrives | 2026-09-26 |
| ADR-2 | Opaque session cookie instead of JWT | Server-side revocation on logout and inactivity expiry are spec requirements; httpOnly cookie removes token handling from the SPA | 2026-09-26 |
| ADR-3 | Derived data computed on read, not stored | Keeps writes trivial and avoids consistency bugs; budgets are achievable with two indexed queries | 2026-09-26 |
| ADR-4 | Store UTC timestamps plus user IANA timezone; server computes local dates | Day boundaries, streaks and schedules must agree regardless of client clock or device | 2026-09-26 |
| ADR-5 | Schedule history kept as rows with `effective_from` | Streaks must evaluate past dates against the schedule active then (spec 005 FR-006) | 2026-09-26 |
| ADR-6 | TanStack Query is the only client cache, no global store | Server state dominates this app; a store would duplicate the cache and invite staleness | 2026-09-26 |
| ADR-7 | Frontend types generated from backend OpenAPI | Single contract (constitution V); drift is caught at type-check time | 2026-09-26 |
| ADR-8 | Reminders evaluated client-side while the app is open | No server push or background workers in v1 (spec 008 FR-002); keeps the backend a plain request/response service | 2026-09-26 |
