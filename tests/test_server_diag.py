"""Tests for the /_diag endpoint security and output."""

import importlib
from fastapi.testclient import TestClient

HEADERS = {"X-API-Key": "secret"}


def _build_client(monkeypatch, allow_diag: bool = False) -> TestClient:
    """Return a TestClient with optional ALLOW_DIAG bypass."""
    if allow_diag:
        monkeypatch.setenv("ALLOW_DIAG", "1")
    else:
        monkeypatch.delenv("ALLOW_DIAG", raising=False)
    import server.middleware as middleware
    import server.main as main
    importlib.reload(middleware)
    importlib.reload(main)
    return TestClient(main.app)


def test_diag_requires_auth_and_masks_paths(monkeypatch) -> None:
    """Unauthenticated requests should be rejected and paths masked in responses."""
    client = _build_client(monkeypatch)

    resp = client.get("/_diag")
    assert resp.status_code == 401

    resp = client.get("/_diag", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()

    assert not data["ui_dir"].startswith("/")
    assert not data["index_html"]["path"].startswith("/")
    assert not data["favicon_ico"]["path"].startswith("/")


def test_diag_allowed_with_env_and_masks_paths(monkeypatch) -> None:
    """ALLOW_DIAG should bypass auth while still masking paths."""
    client = _build_client(monkeypatch, allow_diag=True)

    resp = client.get("/_diag")
    assert resp.status_code == 200
    data = resp.json()

    assert not data["ui_dir"].startswith("/")
    assert not data["index_html"]["path"].startswith("/")
    assert not data["favicon_ico"]["path"].startswith("/")
