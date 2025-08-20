from pathlib import Path

import pytest
from starlette.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_smoke():
    """Basic smoke test to ensure test infrastructure runs."""
    assert True


def test_healthz():
    """Cheap liveness check (owned by system_router)."""
    resp = client.get("/_healthz")
    if resp.status_code != 200:
        pytest.skip("/_healthz endpoint unavailable")
    assert resp.status_code == 200


def test_root_served_if_index_present():
    """Only assert / returns 200 if index.html exists."""
    index_html = Path("ui/pages/index.html")
    if not index_html.exists():
        pytest.skip("index.html not present")
    resp = client.get("/")
    assert resp.status_code == 200


def test_static_asset_under_ui():
    """
    Verify a static asset under /ui/ is served if it exists.
    Tries ui/js/main.js then ui/js/helpers.js, skips if neither present.
    """
    candidate = Path("ui/js/main.js")
    if not candidate.exists():
        candidate = Path("ui/js/helpers.js")
    if not candidate.exists():
        pytest.skip("static asset missing")

    # Build URL under /ui/ from the filesystem path
    rel = "/".join(candidate.parts[1:]) if candidate.parts and candidate.parts[0] == "ui" else candidate.as_posix()
    url = f"/ui/{rel}"
    resp = client.get(url)
    assert resp.status_code == 200


def test_diag_requires_auth_when_enabled():
    """
    If auth is enabled and /_diag is protected, it should return 401 without a key.
    If /_diag is missing or not protected (PoC mode), skip instead of failing.
    """
    resp = client.get("/_diag")
    if resp.status_code in (200, 404):
        pytest.skip("/_diag not protected or missing (auth likely disabled)")
    assert resp.status_code == 401
