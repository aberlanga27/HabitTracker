# Quickstart: Habit Management

## Automated validation

```bash
cd src/backend && ../../.venv/bin/pytest && ../../.venv/bin/ruff check . && ../../.venv/bin/mypy
cd ../frontend && npm run lint && npm run typecheck && npm test
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e   # includes e2e/habits.spec.ts
```

## Manual validation

1. Sign in, open **Habits** in the header.
2. Create "Read 10 pages" with an emoji and a color → it appears in the list and on Today; reload →
   still there (US1-S1). Submit an empty name or 81 characters → inline error (US1-S2).
3. Edit the habit, change the name, Save → updated; Edit again and Cancel → unchanged (US2).
4. Archive it → gone from Today and the active list, shown under "Archived"; Restore → back (US3).
5. Create three habits, use "Move up" on the third twice (keyboard: Tab to it, Enter) → first;
   reload → order kept (US5).
6. Delete a habit → the Delete button stays disabled until you type its exact name; confirm →
   gone; Cancel → nothing removed (US4).
7. API: 51st active habit → `409 HABIT_LIMIT_REACHED` (US1-S3); another user's habit id → `404`.
