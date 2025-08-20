"""Additional server security and rate limit tests."""

from fastapi.testclient import TestClient

from server.main import app
from server import middleware

client = TestClient(app)
HEADERS = {"X-API-Key": "secret"}


def test_root_includes_request_id():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers


def test_css_served_without_auth():
    resp = client.get("/ui/css/styles.css")
    assert resp.status_code == 200
    assert resp.text  # ensure content returned


def test_secure_endpoint_requires_api_key():
    resp = client.get("/devices")
    assert resp.status_code == 401

    resp = client.get("/devices", headers=HEADERS)
    assert resp.status_code == 200


def test_rate_limit_enforced(monkeypatch):
    monkeypatch.setattr(middleware, "RATE_LIMIT", 2)
    middleware._request_log.clear()

    for _ in range(2):
        r = client.get("/devices", headers=HEADERS)
        assert r.status_code == 200
    r = client.get("/devices", headers=HEADERS)
    assert r.status_code == 429
    assert r.headers.get("X-RateLimit-Limit") == "2"
    assert r.headers.get("X-RateLimit-Remaining") == "0"
    assert "X-RateLimit-Reset" in r.headers
