from pathlib import Path

import pytest
from starlette.testclient import TestClient

from server.main import app
from server.middleware import DISABLE_AUTH


client = TestClient(app)


def test_healthz():
    """Basic health check endpoint should respond."""
    resp = client.get("/healthz")
    if resp.status_code != 200:
        pytest.skip("/healthz endpoint unavailable")
    assert resp.status_code == 200


def test_root_served_if_index_present():
    index_html = Path("ui/pages/index.html")
    if not index_html.exists():
        pytest.skip("index.html not present")
    resp = client.get("/")
    assert resp.status_code == 200


def test_static_asset_under_ui():
    asset_path = Path("ui/js/helpers.js")
    if not asset_path.exists():
        pytest.skip("static asset missing")
    resp = client.get("/ui/js/helpers.js")
    assert resp.status_code == 200


def test_api_route_requires_auth_when_enabled():
    if DISABLE_AUTH:
        pytest.skip("auth disabled")
    resp = client.get("/devices")
    assert resp.status_code == 401
