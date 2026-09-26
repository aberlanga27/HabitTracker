# Quickstart: User Accounts

## Prerequisites

- `.venv` with backend deps: `uv pip install --python .venv/bin/python -r src/backend/pyproject.toml --extra dev`
- Frontend deps: `cd src/frontend && npm install`

## Automated validation

```bash
cd src/backend
../../.venv/bin/alembic upgrade head
../../.venv/bin/pytest            # unit + api + contract, coverage gate
../../.venv/bin/ruff check . && ../../.venv/bin/ruff format --check . && ../../.venv/bin/mypy

cd ../frontend
npm run lint && npm run typecheck && npm test
npm run test:e2e                  # starts backend + Vite, runs @p1 journeys with axe
```

## Manual validation

1. Start the backend (`cd src/backend && ../../.venv/bin/uvicorn app.main:app --reload`) and the
   frontend (`cd src/frontend && npm run dev`), open http://localhost:5173.
2. You are redirected to `/sign-in`. Choose "Create an account", register `ana@example.com` with a
   12-character password → the empty dashboard shows `ana@example.com` in the header (US1-S1).
3. Reload → still signed in (US2-S3).
4. Sign out → sign-in screen; open `/` directly → redirected to `/sign-in` (US3).
5. Sign in with a wrong password → "Invalid email or password" (US2-S2). Repeat 5 times → locked out.
6. Register again with `Ana@Example.com` → "Could not register" (US1-S2, case-insensitive email).
