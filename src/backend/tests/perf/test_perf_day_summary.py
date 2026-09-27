"""SC-002: day summary < 150 ms p95 with 50 habits and 10k check-ins."""

import statistics
import time
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import CheckIn
from tests.factories import make_habit, register

NOW = datetime(2026, 9, 26, 12, tzinfo=UTC)


@pytest.mark.perf
def test_sc002_perf_day_summary_p95_under_150ms(client: TestClient, db: Session) -> None:
    user_id = register(client)["id"]
    start = date(2026, 9, 26) - timedelta(days=199)
    for n in range(50):
        habit = make_habit(db, user_id=user_id, created_at=NOW, name=f"Habit {n}", position=n)
        db.add_all(
            CheckIn(habit_id=habit.id, local_date=start + timedelta(days=d), completed_at=NOW)
            for d in range(200)
        )
    db.commit()

    timings = []
    for _ in range(30):
        began = time.perf_counter()
        assert client.get("/api/v1/days/2026-09-26").status_code == 200
        timings.append(time.perf_counter() - began)
    p95 = statistics.quantiles(timings, n=20)[-1]
    assert p95 < 0.150, f"p95 {p95 * 1000:.1f} ms"
