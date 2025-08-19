"""FastAPI application exposing minimal API for Rotterdam."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Response
from pydantic import BaseModel

from devices.discovery import list_detailed_devices
from risk_scoring.risk_score import calculate_risk_score

from .middleware import AuthRateLimitMiddleware
from threading import Thread

app = FastAPI(title="Rotterdam API")
app.add_middleware(AuthRateLimitMiddleware)


class JobRequest(BaseModel):
    """Request body for a job submission."""

    serial: str
    static_metrics: Dict[str, float] | None = None
    dynamic_metrics: Dict[str, float] | None = None
    params: Dict[str, Any] | None = None


_jobs: Dict[str, Dict[str, Any]] = {}


@app.get("/devices")
async def get_devices() -> list[Dict[str, Any]]:
    """Enumerate connected devices.

    If ADB or device discovery fails, return an empty list instead of raising
    so the API remains usable in environments without Android tools."""
    try:
        return list_detailed_devices()
    except Exception:
        return []


def _process_job(job_id: str, req: JobRequest) -> None:
    """Simulate job processing and populate the report."""
    # Simulate some work taking a bit of time
    time.sleep(0.5)
    score = calculate_risk_score(req.static_metrics, req.dynamic_metrics)
    _jobs[job_id]["report"] = {
        "status": "completed",
        "risk": score,
        "params": req.params or {},
    }


@app.post("/jobs")
async def submit_job(req: JobRequest) -> Dict[str, str]:
    """Submit a job for processing and return a job ID."""
    job_id = str(uuid4())
    _jobs[job_id] = {
        "request": req.model_dump(),
        "report": None,
        "created": time.time(),
    }
    Thread(target=_process_job, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id}


@app.get("/jobs")
async def list_jobs() -> list[Dict[str, Any]]:
    """Return all submitted jobs with their status."""
    jobs = []
    for jid, job in _jobs.items():
        jobs.append(
            {
                "job_id": jid,
                "status": "completed" if job["report"] else "pending",
                "created": job["created"],
            }
        )
    return jobs


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    """Return details for a single job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": "completed" if job["report"] else "pending",
        "created": job["created"],
        "request": job["request"],
    }


@app.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str) -> Response:
    """Remove a job and its report."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    del _jobs[job_id]
    return Response(status_code=204)


@app.get("/reports/{job_id}")
async def get_report(job_id: str) -> Dict[str, Any]:
    """Retrieve a report for a given job ID."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["report"] is None:
        return JSONResponse(status_code=202, content={"status": "pending"})
    return {"job_id": job_id, "report": job["report"]}


@app.get("/reports")
async def list_reports() -> list[Dict[str, Any]]:
    """Return all completed reports."""
    reports = []
    for jid, job in _jobs.items():
        if job["report"]:
            reports.append({"job_id": jid, **job["report"]})
    return reports


@app.get("/analytics")
async def get_analytics() -> Dict[str, Any]:
    """Compute simple analytics for completed reports."""
    scores = [job["report"]["risk"]["score"] for job in _jobs.values() if job["report"]]
    if not scores:
        return {
            "average_score": None,
            "reports": 0,
            "min_score": None,
            "max_score": None,
        }
    avg = sum(scores) / len(scores)
    return {
        "average_score": avg,
        "reports": len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
    }


@app.get("/analytics/devices")
async def get_device_analytics() -> list[Dict[str, Any]]:
    """Compute analytics grouped by device serial."""
    per_device: Dict[str, list[float]] = {}
    for job in _jobs.values():
        if job["report"]:
            serial = job["request"].get("serial", "unknown")
            score = job["report"]["risk"]["score"]
            per_device.setdefault(serial, []).append(score)
    results = []
    for serial, scores in per_device.items():
        results.append(
            {
                "serial": serial,
                "reports": len(scores),
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
            }
        )
    return results
