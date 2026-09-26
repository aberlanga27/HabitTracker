"""Small builders for test data. Each test builds exactly what it needs."""

from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.models import Habit, User

DEFAULT_PASSWORD = "correct-horse-battery"


def make_user(
    db: Session,
    *,
    email: str = "ana@example.com",
    password: str = DEFAULT_PASSWORD,
    timezone: str = "UTC",
    created_at: datetime,
) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        timezone=timezone,
        created_at=created_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register(
    client: TestClient,
    *,
    email: str = "ana@example.com",
    password: str = DEFAULT_PASSWORD,
    timezone: str = "UTC",
) -> dict[str, str]:
    """Register through the API; the client keeps the session cookie."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "timezone": timezone},
    )
    assert resp.status_code == 201, resp.text
    body: dict[str, str] = resp.json()
    return body


def make_habit(
    db: Session,
    *,
    user_id: str,
    created_at: datetime,
    name: str = "Read 10 pages",
    position: int = 0,
    archived_at: datetime | None = None,
) -> Habit:
    habit = Habit(
        user_id=user_id,
        name=name,
        position=position,
        archived_at=archived_at,
        created_at=created_at,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def create_habit(client: TestClient, **fields: object) -> dict[str, Any]:
    """Create a habit through the API for the signed-in client."""
    payload: dict[str, object] = {"name": "Read 10 pages", **fields}
    resp = client.post("/api/v1/habits", json=payload)
    assert resp.status_code == 201, resp.text
    body: dict[str, Any] = resp.json()
    return body
