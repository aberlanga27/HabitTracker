from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AuthSession
from tests.factories import register


def test_us3_s1_fr005_sign_out_invalidates_session_server_side(
    client: TestClient, db: Session
) -> None:
    register(client)
    token = client.cookies["habitude_session"]
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    assert (
        'habitude_session=""' in resp.headers["set-cookie"]
        or "Max-Age=0" in resp.headers["set-cookie"]
    )
    assert db.exec(select(AuthSession)).all() == []
    client.cookies.set("habitude_session", token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_us3_s2_signed_out_browser_is_rejected(client: TestClient) -> None:
    register(client)
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_fr005_logout_without_session_is_idempotent(client: TestClient) -> None:
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_fr005_logout_only_removes_the_current_session(client: TestClient, db: Session) -> None:
    register(client)
    other = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "correct-horse-battery"},
    )
    assert other.status_code == 200
    assert len(db.exec(select(AuthSession)).all()) == 2
    client.post("/api/v1/auth/logout")
    assert len(db.exec(select(AuthSession)).all()) == 1
