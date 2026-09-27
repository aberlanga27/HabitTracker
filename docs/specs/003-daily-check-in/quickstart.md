# Quickstart: Daily Check-In

## Automated validation

```bash
cd src/backend && ../../.venv/bin/pytest && ../../.venv/bin/ruff check . && ../../.venv/bin/mypy
cd ../frontend && npm run lint && npm run typecheck && npm test
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e   # includes e2e/check-in.spec.ts
```

## Manual validation

1. Sign in with at least one habit and open Today.
2. Click the habit → it shows ✓ immediately; reload → still completed (US1-S1). Click again →
   uncompleted; reload → uncompleted (US1-S2).
3. Stop the backend and click → the toggle reverts and "Could not save" is announced (US1-S3).
4. Press "Previous day", check in, press "Today" → today's state is separate (US2-S1).
5. "Next day" is disabled on today; "Previous day" is disabled 30 days back. Open
   `/?date=<31 days ago>` → controls disabled with an explanation (US2-S2, US2-S3).
6. On a completed habit choose "Add note", type up to 280 characters, Save → the note shows;
   reload → still there (US3).
7. API: `PUT .../check-ins/<tomorrow>` → `422 DATE_OUT_OF_RANGE`; archived habit → `409`.
