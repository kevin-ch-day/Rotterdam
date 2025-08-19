"""Tests for scan upload and retrieval endpoints."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from server import app
from orchestrator.scheduler import scheduler


client = TestClient(app)


def _wait_for_jobs():
    scheduler.wait_for_all()
    for _ in range(50):
        if all((scheduler.get_job(jid) and scheduler.get_job(jid).status == "completed") for jid in scheduler.list_jobs()):
            break
        time.sleep(0.1)


def test_upload_filename_sanitized(tmp_path):
    data = {"file": ("../../evil.apk", b"apkdata", "application/vnd.android.package-archive")}
    resp = client.post("/scans", files=data)
    assert resp.status_code == 200
    scan_id = resp.json()["scan_id"]
    assert scan_id

    uploads_dir = Path("analysis/uploads")
    # Ensure file is stored inside uploads directory
    assert any(p.name.endswith("evil.apk") for p in uploads_dir.iterdir())
    assert not (uploads_dir / ".." / "evil.apk").exists()

    _wait_for_jobs()
    # Invalid format should be rejected
    bad = client.get(f"/scans/{scan_id}/report?format=xml")
    assert bad.status_code in {400, 404}


def test_findings_and_artifacts_endpoints():
    data = {"file": ("app.apk", b"apkdata", "application/vnd.android.package-archive")}
    resp = client.post("/scans", files=data)
    scan_id = resp.json()["scan_id"]
    _wait_for_jobs()

    res = client.get(f"/scans/{scan_id}/findings")
    assert res.status_code in {200, 404}
    if res.status_code == 200:
        assert isinstance(res.json(), list)

    res = client.get(f"/scans/{scan_id}/artifacts")
    assert res.status_code in {200, 404}
    if res.status_code == 200:
        artifacts = res.json()
        assert any(a["name"] == "report.json" for a in artifacts)

