from fastapi.testclient import TestClient


def test_unknown_route_returns_error_envelope(client: TestClient) -> None:
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "NOT_FOUND", "message": "Not Found", "details": {}}}


def test_state_changing_request_without_requested_with_header_is_forbidden(
    client: TestClient,
) -> None:
    del client.headers["X-Requested-With"]
    resp = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "correct-horse-1"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_validation_errors_use_envelope_with_fields(client: TestClient) -> None:
    resp = client.post("/api/v1/auth/register", json={"email": "ana@example.com"})
    assert resp.status_code == 422
    body = resp.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert any(field["loc"][-1] == "password" for field in body["details"]["fields"])
