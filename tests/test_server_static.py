"""Tests for serving the web UI and static assets."""

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "secret"}


def test_root_serves_index_page():
    resp = client.get("/", headers=HEADERS)
    assert resp.status_code == 200
    assert "Rotterdam Dashboard" in resp.text


def test_static_files_served():
    resp = client.get("/static/js/helpers.js", headers=HEADERS)
    assert resp.status_code == 200
    assert "window.api" in resp.text
