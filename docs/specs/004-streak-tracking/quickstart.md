# Quickstart: Streak Tracking

## Automated validation

```bash
cd src/backend && ../../.venv/bin/pytest && ../../.venv/bin/pytest -m perf --no-cov && ../../.venv/bin/ruff check . && ../../.venv/bin/mypy
cd ../frontend && npm run lint && npm run typecheck && npm test
PLAYWRIGHT_CHANNEL=chrome npm run test:e2e   # includes e2e/streaks.spec.ts
```

## Manual validation

1. Create a daily habit. On Today use "Previous day" twice, check in on each day, then check in
   today → the 🔥 badge reads 3 (US1-S1). Undo today → 2 (not broken until the day ends, US1-S2).
2. Leave a gap two days ago → the badge counts only the days after the gap (US1-S3).
3. Open the habit (click its name on Habits) → "Longest streak" shows the best run and its dates
   (US2).
4. A Mon/Wed/Fri habit completed Mon and Wed shows 2 on Thursday; missing Friday shows 0 on
   Saturday (US3).
5. Archive a habit → its streak stays frozen at the archive date.
