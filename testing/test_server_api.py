"""Tests for the FastAPI server endpoints."""

import time

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)
HEADERS = {"X-API-Key": "secret"}


def test_job_lifecycle():
    # Devices endpoint should always return a list
    resp = client.get("/devices", headers=HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # Submit a job with some metrics
    payload = {
        "serial": "ABC",
        "static_metrics": {"permission_density": 0.6},
        "dynamic_metrics": {"permission_invocation_count": 15},
    }
    resp = client.post("/jobs", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    assert job_id

    # Report should initially be pending
    resp = client.get(f"/reports/{job_id}", headers=HEADERS)
    assert resp.status_code == 202

    # After background task completes, report should be available
    time.sleep(0.6)
    resp = client.get(f"/reports/{job_id}", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["report"]["status"] == "completed"
    assert "risk" in data["report"]
    assert "score" in data["report"]["risk"]

    # Jobs endpoint should list the completed job
    resp = client.get("/jobs", headers=HEADERS)
    assert resp.status_code == 200
    jobs = resp.json()
    assert any(j["job_id"] == job_id and j["status"] == "completed" for j in jobs)

    # Job detail endpoint should return information
    resp = client.get(f"/jobs/{job_id}", headers=HEADERS)
    assert resp.status_code == 200
    job_detail = resp.json()
    assert job_detail["job_id"] == job_id
    assert job_detail["status"] == "completed"

    # Reports endpoint should include the job's report
    resp = client.get("/reports", headers=HEADERS)
    assert resp.status_code == 200
    reports = resp.json()
    assert any(r["job_id"] == job_id for r in reports)

    # Analytics endpoint should compute averages
    resp = client.get("/analytics", headers=HEADERS)
    assert resp.status_code == 200
    analytics = resp.json()
    assert analytics["reports"] >= 1
    assert analytics["average_score"] is not None
    assert analytics["min_score"] is not None
    assert analytics["max_score"] is not None

    # Device analytics should group by serial
    resp = client.get("/analytics/devices", headers=HEADERS)
    assert resp.status_code == 200
    device_stats = resp.json()
    assert any(s["serial"] == "ABC" and s["reports"] >= 1 for s in device_stats)

    # Deleting a job removes it
    resp = client.delete(f"/jobs/{job_id}", headers=HEADERS)
    assert resp.status_code == 204
    resp = client.get(f"/jobs/{job_id}", headers=HEADERS)
    assert resp.status_code == 404
    resp = client.get(f"/reports/{job_id}", headers=HEADERS)
    assert resp.status_code == 404

