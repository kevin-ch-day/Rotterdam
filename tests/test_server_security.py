"""Additional server security and rate limit tests."""

import dataclasses

from fastapi.testclient import TestClient

from server.main import app
from server.middleware import AuthRateLimitMiddleware
from server.middleware.policies import SimpleApiPolicy
from server.middleware.rate_limiter import RateLimiter

client = TestClient(app)
HEADERS = {"X-API-Key": "secret"}


def _get_auth_middleware(app):
    stack = app.middleware_stack
    while hasattr(stack, "app"):
        if isinstance(stack, AuthRateLimitMiddleware):
            return stack
        stack = stack.app
    raise RuntimeError("AuthRateLimitMiddleware not found")


def _configure_auth(rate_limit: int = 60):
    auth = _get_auth_middleware(client.app)
    new_settings = dataclasses.replace(
        auth.settings,
        disable_auth=False,
        protect_prefixes=("/devices",),
        rate_limit=rate_limit,
    )
    auth.settings = new_settings
    auth.policy = SimpleApiPolicy(new_settings)
    auth.limiter = RateLimiter(new_settings)


def test_root_includes_request_id():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers


def test_css_served_without_auth():
    resp = client.get("/ui/css/styles.css")
    assert resp.status_code == 200
    assert resp.text  # ensure content returned


def test_secure_endpoint_requires_api_key():
    _configure_auth()
    resp = client.get("/devices")
    assert resp.status_code == 401

    resp = client.get("/devices", headers=HEADERS)
    assert resp.status_code == 200


def test_rate_limit_enforced():
    _configure_auth(rate_limit=2)
    for _ in range(2):
        r = client.get("/devices", headers=HEADERS)
        assert r.status_code == 200
    r = client.get("/devices", headers=HEADERS)
    assert r.status_code == 429
    assert r.headers.get("X-RateLimit-Limit") == "2"
    assert r.headers.get("X-RateLimit-Remaining") == "0"
    assert "X-RateLimit-Reset" in r.headers
