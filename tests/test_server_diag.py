"""Tests for the /_diag endpoint security and output."""

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)
HEADERS = {"X-API-Key": "secret"}


def test_diag_requires_auth_and_masks_paths() -> None:
    """Unauthenticated requests should be rejected and paths masked in responses."""
    resp = client.get("/_diag")
    assert resp.status_code == 401

    resp = client.get("/_diag", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()

    assert not data["ui_dir"].startswith("/")
    assert not data["index_html"]["path"].startswith("/")
    assert not data["favicon_ico"]["path"].startswith("/")
