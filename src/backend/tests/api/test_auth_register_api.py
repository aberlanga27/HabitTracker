import logging

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AuthSession, User
from tests.factories import register

PASSWORD = "twelve-chars"


def test_us1_s1_register_creates_account_and_signs_in(client: TestClient, db: Session) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": PASSWORD, "timezone": "America/Monterrey"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ana@example.com"
    assert body["timezone"] == "America/Monterrey"
    assert body["created_at"].endswith("Z")
    assert "password" not in body and "password_hash" not in body
    assert "habitude_session" in resp.cookies
    assert db.exec(select(AuthSession)).one().user_id == body["id"]
    assert client.get("/api/v1/auth/me").json()["email"] == "ana@example.com"


def test_fr003_session_cookie_is_httponly_and_samesite_lax(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": PASSWORD}
    )
    cookie = resp.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie


def test_r11_timezone_defaults_to_utc(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": PASSWORD}
    )
    assert resp.json()["timezone"] == "UTC"


def test_us1_s2_fr008_duplicate_email_rejected_generically(client: TestClient) -> None:
    register(client, email="ana@example.com")
    client.cookies.clear()
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": PASSWORD}
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == {
        "code": "REGISTRATION_FAILED",
        "message": "Could not register",
        "details": {},
    }


def test_edge_email_compared_case_insensitively_on_register(client: TestClient) -> None:
    register(client, email="ana@example.com")
    client.cookies.clear()
    resp = client.post(
        "/api/v1/auth/register", json={"email": "Ana@Example.com", "password": PASSWORD}
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["message"] == "Could not register"


def test_edge_email_stored_lowercase(client: TestClient) -> None:
    body = register(client, email="  Ana@Example.COM ")
    assert body["email"] == "ana@example.com"


@pytest.mark.parametrize("password", ["short", "123456789"])
def test_us1_s3_fr001_password_shorter_than_10_rejected(client: TestClient, password: str) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": password}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_fr001_password_of_exactly_10_accepted(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": "1234567890"}
    )
    assert resp.status_code == 201


def test_r4_password_longer_than_128_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": "x" * 129}
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("email", ["not-an-email", "a@b", "@example.com", "a b@example.com"])
def test_r5_malformed_email_rejected(client: TestClient, email: str) -> None:
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 422


def test_r11_invalid_timezone_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": PASSWORD, "timezone": "Mars/Olympus"},
    )
    assert resp.status_code == 422


def test_fr002_sc004_password_stored_hashed_and_never_logged(
    client: TestClient, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    register(client, email="ana@example.com", password=PASSWORD)
    user = db.exec(select(User)).one()
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    assert PASSWORD not in caplog.text
