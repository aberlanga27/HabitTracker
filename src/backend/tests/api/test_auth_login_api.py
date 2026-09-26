from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AuthSession, FailedLogin
from tests.factories import DEFAULT_PASSWORD, register
from tests.fakes import FrozenClock


def _login(client: TestClient, email: str, password: str) -> int:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return int(resp.status_code)


def _registered_signed_out(client: TestClient, email: str = "ana@example.com") -> None:
    register(client, email=email)
    client.post("/api/v1/auth/logout")
    client.cookies.clear()


def test_us2_s1_fr003_correct_credentials_sign_in(client: TestClient) -> None:
    _registered_signed_out(client)
    resp = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": DEFAULT_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "ana@example.com"
    assert "habitude_session" in resp.cookies


def test_edge_sign_in_email_is_case_insensitive(client: TestClient) -> None:
    _registered_signed_out(client)
    assert _login(client, "ANA@example.com", DEFAULT_PASSWORD) == 200


def test_us2_s2_fr008_wrong_password_is_generic(client: TestClient) -> None:
    _registered_signed_out(client)
    resp = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "wrong-password-1"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password",
        "details": {},
    }


def test_fr008_unknown_email_is_indistinguishable_from_wrong_password(
    client: TestClient,
) -> None:
    resp = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": DEFAULT_PASSWORD}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid email or password"


def test_us2_s3_session_survives_reload(client: TestClient) -> None:
    register(client)
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_fr006_me_without_session_is_unauthenticated(client: TestClient) -> None:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_fr006_me_with_forged_token_is_unauthenticated(client: TestClient) -> None:
    client.cookies.set("habitude_session", "forged-token")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_us2_s4_fr004_session_expires_after_30_idle_days(
    client: TestClient, clock: FrozenClock, db: Session
) -> None:
    register(client)
    clock.advance(timedelta(days=30))
    assert client.get("/api/v1/auth/me").status_code == 401
    assert db.exec(select(AuthSession)).all() == []


def test_fr004_activity_slides_the_expiry_window(client: TestClient, clock: FrozenClock) -> None:
    register(client)
    clock.advance(timedelta(days=29))
    assert client.get("/api/v1/auth/me").status_code == 200
    clock.advance(timedelta(days=29))
    assert client.get("/api/v1/auth/me").status_code == 200


def test_fr007_five_failures_in_15_minutes_lock_the_email(
    client: TestClient, clock: FrozenClock
) -> None:
    _registered_signed_out(client)
    for _ in range(5):
        assert _login(client, "ana@example.com", "wrong-password-1") == 401
        clock.advance(timedelta(minutes=2))
    resp = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": DEFAULT_PASSWORD}
    )
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "LOCKED_OUT"


def test_fr007_lockout_lifts_after_15_minutes(client: TestClient, clock: FrozenClock) -> None:
    _registered_signed_out(client)
    for _ in range(5):
        _login(client, "ana@example.com", "wrong-password-1")
    clock.advance(timedelta(minutes=14))
    assert _login(client, "ana@example.com", DEFAULT_PASSWORD) == 429
    clock.advance(timedelta(minutes=1))
    assert _login(client, "ana@example.com", DEFAULT_PASSWORD) == 200


def test_fr007_failures_spread_over_more_than_15_minutes_do_not_lock(
    client: TestClient, clock: FrozenClock
) -> None:
    _registered_signed_out(client)
    for _ in range(5):
        _login(client, "ana@example.com", "wrong-password-1")
        clock.advance(timedelta(minutes=4))
    assert _login(client, "ana@example.com", DEFAULT_PASSWORD) == 200


def test_fr007_lockout_is_per_email_and_case_insensitive(
    client: TestClient, clock: FrozenClock
) -> None:
    _registered_signed_out(client, "ana@example.com")
    _registered_signed_out(client, "ben@example.com")
    for _ in range(5):
        _login(client, "ANA@example.com", "wrong-password-1")
    assert _login(client, "ana@example.com", DEFAULT_PASSWORD) == 429
    assert _login(client, "ben@example.com", DEFAULT_PASSWORD) == 200


def test_fr007_successful_sign_in_clears_failures(client: TestClient, db: Session) -> None:
    _registered_signed_out(client)
    for _ in range(4):
        _login(client, "ana@example.com", "wrong-password-1")
    assert _login(client, "ana@example.com", DEFAULT_PASSWORD) == 200
    assert db.exec(select(FailedLogin)).all() == []


def test_fr007_unknown_email_also_locks(client: TestClient) -> None:
    for _ in range(5):
        assert _login(client, "ghost@example.com", "wrong-password-1") == 401
    assert _login(client, "ghost@example.com", "wrong-password-1") == 429
