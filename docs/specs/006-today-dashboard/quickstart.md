# Quickstart: Today Dashboard

## Automated validation

```bash
cd src/backend && ../../.venv/bin/pytest && ../../.venv/bin/pytest -m perf --no-cov
cd ../frontend && npm run lint && npm run typecheck && npm test && npm run build
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e   # includes e2e/today.spec.ts
```

## Manual validation

1. New account → Today shows "Create your first habit" (US1-S2).
2. Create 5 daily habits, complete 3 → "3 of 5 habits done" and the bar is 60% (US1-S1); the
   completed ones sit under "Done" (US3).
3. Complete the other 2 → "All done for today" (US1-S3).
4. "Previous day" → yesterday with its own state; "Jump to today" returns (US2).
5. Keyboard only: Tab through day navigation and every habit toggle, Space/Enter toggles; a
   screen reader announces the new progress (FR-006).
6. Leave the tab open across local midnight → the header switches to the new day.
