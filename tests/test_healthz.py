from fastapi.testclient import TestClient

from server.main import app


def test_healthz_endpoint():
    """Ensure the liveness endpoint responds."""
    with TestClient(app) as client:
        resp = client.get("/_healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
