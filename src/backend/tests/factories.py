"""Small builders for test data. Each test builds exactly what it needs."""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.models import User

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
