# Implementation Plan: User Accounts

**Branch**: `001-user-accounts` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/specs/001-user-accounts/spec.md`

## Summary

Local email + password accounts with server-side opaque sessions stored in an `httpOnly`
cookie. Visitors register (auto sign-in), sign in, stay signed in across reloads for up to
30 days of inactivity, and sign out (server-side invalidation). Five failed sign-ins for one
email in 15 minutes lock that email for 15 minutes. Because this is the first feature, the
plan also bootstraps both projects (FastAPI backend, React frontend), the shared error
envelope, the injected clock, Alembic migrations, the OpenAPI snapshot, and test harnesses
that every later spec reuses.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5 strict (frontend), Node 22 LTS

**Primary Dependencies**: FastAPI, SQLModel, Alembic, uvicorn, argon2-cffi, pydantic-settings;
React 19, Vite, React Router (data router), TanStack Query

**Storage**: SQLite file (`habitude.db`), schema managed by Alembic

**Testing**: pytest + FastAPI `TestClient` (httpx) + pytest-cov; Vitest + Testing Library +
MSW + axe-core; Playwright + @axe-core/playwright for P1 journeys

**Target Platform**: Developer laptop (macOS/Linux), evergreen browsers

**Project Type**: Web application (REST API + SPA)

**Performance Goals**: Sign-in < 500 ms p95 locally (SC-003); any endpoint < 200 ms p95

**Constraints**: No external services, no telemetry; passwords never logged or stored in
plaintext (SC-004); generic auth error messages (FR-008)

**Scale/Scope**: Single-tenant local deployment, a handful of users

## Constitution Check

*Validated against constitution v1.0.0.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-First | PASS | spec.md has no open clarifications; this plan + tasks.md precede code. |
| II. Vertical Slices | PASS | Each story ships API + UI + tests; US1/US2 form the MVP slice. |
| III. Test-First | PASS | tasks.md orders failing tests before implementation for every FR. |
| IV. Simplicity | PASS | No JWT, no auth library, no global store; dependencies justified below. |
| V. Explicit Contracts | PASS | OpenAPI served at `/api/v1/openapi.json`, snapshot committed at `src/backend/openapi.json`, frontend types generated from it. |
| VI. Local-First | PASS | SQLite only; no network calls beyond the local API. |
| VII. AI-Assisted, Human-Accountable | PASS | Commits and PR cite `001` and FR ids. |

Post-design re-check: PASS (no new violations introduced by data model or contracts).

## Project Structure

### Documentation (this feature)

```text
docs/specs/001-user-accounts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/auth.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/backend/
├── pyproject.toml            # deps + ruff/mypy/pytest config
├── alembic.ini
├── openapi.json              # committed OpenAPI snapshot (contract test compares)
├── scripts/export_openapi.py
├── app/
│   ├── main.py               # create_app()
│   ├── core/                 # config, db (UTCDateTime), clock, ids (uuid7), errors, logging,
│   │                         # security (argon2, tokens), auth (current user dep), csrf
│   ├── models/               # user.py, auth_session.py, failed_login.py
│   ├── schemas/auth.py
│   ├── services/auth.py
│   ├── routers/auth.py
│   └── migrations/           # Alembic env + versions/
└── tests/
    ├── conftest.py           # migrated template DB copied per test, FrozenClock, client
    ├── factories.py
    ├── unit/
    ├── api/
    └── contract/

src/frontend/
├── package.json, vite.config.ts, tsconfig*.json, eslint.config.js, playwright.config.ts
├── e2e/auth.spec.ts
└── src/
    ├── main.tsx
    ├── app/                  # App.tsx, routes.tsx, providers.tsx, layout/ (AppShell, ProtectedRoute, GuestRoute)
    ├── features/auth/        # api.ts, hooks/, components/ (SignInForm, RegisterForm), pages
    ├── features/today/       # placeholder TodayPage (empty dashboard) until spec 006
    ├── shared/lib/           # apiClient.ts, queryKeys.ts
    ├── shared/theme/tokens.css
    ├── shared/types/api.generated.ts
    └── test/                 # setup.ts, msw server, render helper
```

**Structure Decision**: Web application layout from `docs/architecture.md`, using the backend
module names from `docs/coding-standards.md` (`routers/` rather than `api/v1/`) because the
coding standards are the more specific style authority.

## Complexity Tracking

No constitution violations. Dependency justifications (Principle IV):

| Dependency | Justification |
|---|---|
| argon2-cffi | FR-002 requires a modern adaptive hash; argon2id is mandated by coding standards. |
| pydantic-settings | Typed `HABITUDE_*` env configuration without hand-rolled parsing. |
| pytest-cov | Enforces the 85% coverage gate from the constitution. |
| msw | Network-boundary mocking mandated by `docs/testing.md`. |
| axe-core, @axe-core/playwright | Automated WCAG checks mandated by the constitution. |
| openapi-typescript | Generates frontend types from the OpenAPI contract (Principle V, ADR-7). |
| eslint plugins (typescript-eslint, react-hooks, jsx-a11y, import), prettier | Lint/format rules listed in `docs/coding-standards.md`. |
