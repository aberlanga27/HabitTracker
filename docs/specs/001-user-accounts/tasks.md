---
description: "Task list for spec 001 User Accounts"
---

# Tasks: User Accounts

**Input**: Design documents from `docs/specs/001-user-accounts/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth.openapi.yaml

**Tests**: Required. Constitution Principle III (Test-First) is non-negotiable; every FR maps to
at least one test written before its implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 Register, US2 Sign in and stay signed in, US3 Sign out

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create backend project config with deps and ruff/mypy/pytest/coverage settings in src/backend/pyproject.toml
- [ ] T002 [P] Create frontend project (package.json, tsconfig*.json, vite.config.ts, index.html, eslint.config.js, .prettierrc.json) in src/frontend/
- [ ] T003 [P] Configure Vitest (jsdom, setup file, MSW server, coverage thresholds 80%) in src/frontend/vitest.config.ts and src/frontend/src/test/
- [ ] T004 [P] Configure Playwright with backend + Vite web servers and axe in src/frontend/playwright.config.ts
- [ ] T005 Update ignore patterns (Python, Node, Playwright) in .gitignore

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T006 Settings (`HABITUDE_DATABASE_URL`, `HABITUDE_SESSION_TTL_DAYS`, `HABITUDE_CORS_ORIGINS`, `HABITUDE_LOG_LEVEL`, `HABITUDE_COOKIE_SECURE`) in src/backend/app/core/config.py and src/backend/.env.example
- [ ] T007 [P] Unit tests for `local_date`, `FrozenClock` and uuid7 ordering in src/backend/tests/unit/test_clock.py and src/backend/tests/unit/test_ids.py
- [ ] T008 [P] Clock protocol, `SystemClock`, `get_clock`, `local_date(now_utc, tz)` in src/backend/app/core/clock.py
- [ ] T009 [P] UUIDv7 helper in src/backend/app/core/ids.py
- [ ] T010 Engine, `get_session`, `UTCDateTime` type, SQLite foreign keys pragma in src/backend/app/core/db.py
- [ ] T011 [P] Domain errors and handlers producing `{"error": {"code","message","details"}}` (UPPER_SNAKE codes, `VALIDATION_ERROR` with `details.fields`) in src/backend/app/core/errors.py
- [ ] T012 [P] Logging setup in src/backend/app/core/logging.py
- [ ] T013 [P] CSRF middleware requiring `X-Requested-With` on POST/PUT/PATCH/DELETE under /api in src/backend/app/core/csrf.py
- [ ] T014 Alembic setup (alembic.ini, env.py reading configured URL or settings) in src/backend/alembic.ini and src/backend/app/migrations/
- [ ] T015 App factory with CORS, CSRF, error handlers, `/api/v1` prefix and OpenAPI at `/api/v1/openapi.json` in src/backend/app/main.py
- [ ] T016 Test harness: migrated template DB copied per test, `FrozenClock` override, `client` with `X-Requested-With`, fast argon2 hasher in src/backend/tests/conftest.py and src/backend/tests/factories.py
- [ ] T017 [P] API tests for error envelope on unknown route and CSRF rejection in src/backend/tests/api/test_errors_api.py
- [ ] T018 OpenAPI export script and contract snapshot test in src/backend/scripts/export_openapi.py and src/backend/tests/contract/test_openapi_snapshot.py
- [ ] T019 [P] Design tokens (semantic colors, spacing, radii, focus ring, light/dark) in src/frontend/src/shared/theme/tokens.css and src/frontend/src/shared/theme/global.css
- [ ] T020 [P] `apiClient` (credentials include, `X-Requested-With`, `ApiError`) with tests in src/frontend/src/shared/lib/apiClient.ts and src/frontend/src/shared/lib/apiClient.test.ts
- [ ] T021 [P] Query keys factory in src/frontend/src/shared/lib/queryKeys.ts
- [ ] T022 Providers (QueryClient with 401 → `me=null`), router, App, main in src/frontend/src/app/

**Checkpoint**: Backend boots with `/api/v1/openapi.json`; frontend builds and renders.

## Phase 3: User Story 1 - Register a New Account (P1) 🎯 MVP

**Goal**: A visitor registers with email + password and lands signed in on the empty dashboard.

**Independent Test**: Register `ana@example.com` with a 12-char password; dashboard shows the email in the header.

### Tests for User Story 1 (write first, confirm failing)

- [ ] T023 [P] [US1] Unit tests for password hashing (argon2id, verify, no plaintext) and email normalization in src/backend/tests/unit/test_security.py
- [ ] T024 [P] [US1] API tests: register creates user + session cookie (FR-001, FR-003); duplicate and case-variant email → 400 "Could not register" (FR-008); password < 10 → 422; invalid timezone → 422; stored hash is argon2id and password never logged (FR-002, SC-004) in src/backend/tests/api/test_auth_register_api.py
- [ ] T025 [P] [US1] Component tests: inline error for password < 10 without submitting; successful submit navigates to dashboard; server error shows "Could not register"; no axe violations in src/frontend/src/features/auth/components/RegisterForm.test.tsx

### Implementation for User Story 1

- [ ] T026 [P] [US1] `User` model (email ≤ 254 unique lowercase, password_hash, timezone default `UTC`, created_at) in src/backend/app/models/user.py
- [ ] T027 [P] [US1] `AuthSession` model (token_hash unique, user_id FK cascade, created_at, last_used_at, expires_at) in src/backend/app/models/auth_session.py
- [ ] T028 [US1] Migration creating `user` and `auth_session` in src/backend/app/migrations/versions/0001_user_accounts.py
- [ ] T029 [P] [US1] Password hashing and token helpers in src/backend/app/core/security.py
- [ ] T030 [P] [US1] Schemas `RegisterRequest` (password 10–128), `LoginRequest`, `UserRead` in src/backend/app/schemas/auth.py
- [ ] T031 [US1] `register` and `create_session` services in src/backend/app/services/auth.py
- [ ] T032 [US1] `POST /api/v1/auth/register` setting the `habitude_session` cookie in src/backend/app/routers/auth.py
- [ ] T033 [US1] Regenerate OpenAPI snapshot and frontend types (`npm run gen:api`) in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts
- [ ] T034 [US1] Auth API functions and hooks (`useMe`, `useRegister`) in src/frontend/src/features/auth/api.ts and src/frontend/src/features/auth/hooks/
- [ ] T035 [US1] `RegisterForm` and `RegisterPage` (labels, inline errors, timezone from `Intl`) in src/frontend/src/features/auth/components/
- [ ] T036 [US1] `AppShell` header with user email and placeholder empty `TodayPage` in src/frontend/src/app/layout/AppShell.tsx and src/frontend/src/features/today/TodayPage.tsx

**Checkpoint**: US1 demonstrable end-to-end.

## Phase 4: User Story 2 - Sign In and Stay Signed In (P1) 🎯 MVP

**Goal**: Returning users sign in and stay signed in across reloads until sign-out or 30 idle days.

**Independent Test**: Register, reload, still signed in.

### Tests for User Story 2 (write first, confirm failing)

- [ ] T037 [P] [US2] API tests: correct credentials → 200 + cookie, case-insensitive email (FR-003); wrong password and unknown email → 401 "Invalid email or password" (FR-008); `/auth/me` with cookie → 200, without → 401 (FR-006); session idle 30 days → 401 and row deleted, activity refreshes expiry (FR-004); 5 failures in 15 min → 429 even with correct password, unlocked after 15 min, success clears failures (FR-007) in src/backend/tests/api/test_auth_login_api.py
- [ ] T038 [P] [US2] Component tests: wrong credentials show "Invalid email or password"; success navigates to `next`; protected route redirects to `/sign-in?next=` when `/auth/me` is 401 in src/frontend/src/features/auth/components/SignInForm.test.tsx and src/frontend/src/app/layout/ProtectedRoute.test.tsx

### Implementation for User Story 2

- [ ] T039 [P] [US2] `FailedLogin` model and migration in src/backend/app/models/failed_login.py and src/backend/app/migrations/versions/0002_failed_login.py
- [ ] T040 [US2] `authenticate` with lockout and `resolve_session` with sliding 30-day expiry in src/backend/app/services/auth.py
- [ ] T041 [US2] `get_current_user` dependency (`CurrentUser`) in src/backend/app/core/auth.py
- [ ] T042 [US2] `POST /api/v1/auth/login` and `GET /api/v1/auth/me` in src/backend/app/routers/auth.py
- [ ] T043 [US2] `useLogin` hook, `SignInForm`, `SignInPage`, `ProtectedRoute`, `GuestRoute` in src/frontend/src/features/auth/ and src/frontend/src/app/layout/
- [ ] T044 [US2] Regenerate OpenAPI snapshot and frontend types in src/backend/openapi.json and src/frontend/src/shared/types/api.generated.ts

**Checkpoint**: US1 + US2 work independently.

## Phase 5: User Story 3 - Sign Out (P2)

**Goal**: Sign out invalidates the session server-side and returns to sign-in.

**Independent Test**: Sign in, sign out, open `/` → redirected to `/sign-in`.

### Tests for User Story 3 (write first, confirm failing)

- [ ] T045 [P] [US3] API tests: logout deletes session and clears cookie, old token then gets 401 (FR-005); logout without session → 204 in src/backend/tests/api/test_auth_logout_api.py
- [ ] T046 [P] [US3] Component test: "Sign out" button calls logout and shows sign-in screen in src/frontend/src/app/layout/AppShell.test.tsx

### Implementation for User Story 3

- [ ] T047 [US3] `logout` service and `POST /api/v1/auth/logout` in src/backend/app/services/auth.py and src/backend/app/routers/auth.py
- [ ] T048 [US3] `useLogout` hook and "Sign out" button in src/frontend/src/features/auth/hooks/use-logout.ts and src/frontend/src/app/layout/AppShell.tsx

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T049 [P] SC-002 guard: test that every non-auth route in the OpenAPI document rejects unauthenticated requests in src/backend/tests/api/test_protected_routes_api.py
- [ ] T050 [P] Playwright @p1 journeys (register → dashboard → reload → sign out; wrong password) with axe and a keyboard-only pass in src/frontend/e2e/auth.spec.ts
- [ ] T051 Update commands in AGENTS.md, README.md, docs/testing.md; mark spec Implemented in docs/specs/001-user-accounts/spec.md and docs/specs/README.md
- [ ] T052 Run quickstart.md validation (ruff, mypy, pytest with coverage, lint, typecheck, vitest, playwright)

## Dependencies & Execution Order

- Setup (T001–T005) → Foundational (T006–T022) → US1 → US2 → US3 → Polish.
- US2 reuses the `User`/`AuthSession` models from US1; US3 reuses `resolve_session` from US2.
- Within each story: tests → models → migration → services → routers → OpenAPI/types → UI.

## Parallel Example: User Story 1

```text
Task: T023 unit tests for security helpers
Task: T024 API tests for register
Task: T025 RegisterForm component tests
```

## Implementation Strategy

MVP = US1 + US2 (both P1). US3 (P2) ships in the same PR because it is small and required for
shared devices. Validate with quickstart.md before opening the PR.
