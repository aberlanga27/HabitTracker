# Quickstart: Habit Schedules

## Automated validation

```bash
cd src/backend && ../../.venv/bin/alembic upgrade head && ../../.venv/bin/pytest && ../../.venv/bin/ruff check . && ../../.venv/bin/mypy
cd ../frontend && npm run lint && npm run typecheck && npm test
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e   # includes e2e/schedules.spec.ts
```

## Manual validation

1. Create a habit without touching the schedule → "Every day" in the list; it appears on Today
   and on every previous day (US1).
2. Create "Gym" with **Specific days** Mon/Wed/Fri. Navigate Today to a Tuesday → not listed; a
   Wednesday → listed (US2-S1). Choose Specific days with none ticked → "Choose at least one day"
   and nothing is saved (US2-S2).
3. Create "Run" with **3 times per week**. Check it in on two days this week → Today shows
   "2 of 3 this week" (US3-S1). After a third day, the next day shows "Done for this week" (US3-S2).
4. Edit a habit's schedule → it applies from today; earlier days keep the old rule and all
   check-ins remain (US4).
5. API: `GET /api/v1/days/2026-09-29` lists only due / done-for-week habits.
