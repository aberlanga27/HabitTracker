"""SC-002: every protected route rejects unauthenticated requests."""

import re

from fastapi import FastAPI
from fastapi.testclient import TestClient

PUBLIC_ROUTES = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
}


def _protected_routes(app: FastAPI) -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            key = (method.upper(), path)
            if key not in PUBLIC_ROUTES:
                routes.append(key)
    return routes


def _concrete(path: str) -> str:
    def value(match: re.Match[str]) -> str:
        return "2026-09-26" if "date" in match.group(1) else "00000000-0000-7000-8000-000000000000"

    return re.sub(r"\{([^}]+)\}", value, path)


def test_sc002_all_protected_routes_reject_unauthenticated(
    app: FastAPI, client: TestClient
) -> None:
    routes = _protected_routes(app)
    assert ("GET", "/api/v1/auth/me") in routes
    for method, path in routes:
        resp = client.request(method, _concrete(path), json={})
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"
        assert resp.json()["error"]["code"] == "UNAUTHENTICATED"
