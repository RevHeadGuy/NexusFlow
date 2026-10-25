"""Shared pytest fixtures for the NexusFlow backend test suite.

The API is gated by :class:`app.security.IdentityAndProjectAccessMiddleware`,
which rejects any request without a valid bearer token. The phase tests predate
that auth layer and issue unauthenticated calls through a module-level
``TestClient``. Rather than rewrite every test, this module registers a single
account once per test session and transparently attaches its bearer token to
every outgoing request, leaving the public endpoints (health, register, login)
untouched.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

from app.main import app

# Paths that must stay unauthenticated. The middleware treats these as public,
# and register/login cannot carry a token because none exists yet.
_PUBLIC_PATHS = {"/health", "/auth/register", "/auth/login", "/docs", "/redoc", "/openapi.json"}


def _register_test_account() -> str:
    """Create a fresh account and return its bearer access token."""
    client = TestClient(app)
    email = f"tester-{uuid.uuid4().hex[:12]}@nexusflow.test"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "display_name": "Test User",
            "password": "test-password-123",
        },
    )
    assert response.status_code == 201, f"Test account setup failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def authenticated_client(request):
    """Attach a bearer token to every ``TestClient`` request for the session.

    All phase tests build their own ``TestClient(app)`` at import time and call
    the API directly. We patch ``TestClient.request`` so those calls carry the
    session's access token without each test having to log in. Public endpoints
    keep whatever authorization the caller supplied (usually none).
    """
    token = _register_test_account()
    original_request = StarletteTestClient.request

    def request_with_auth(self, method, url, *args, **kwargs):
        path = str(url).split("?", 1)[0].rstrip("/") or "/"
        if path not in _PUBLIC_PATHS:
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("Authorization", f"Bearer {token}")
            kwargs["headers"] = headers
        return original_request(self, method, url, *args, **kwargs)

    StarletteTestClient.request = request_with_auth
    try:
        yield token
    finally:
        StarletteTestClient.request = original_request
