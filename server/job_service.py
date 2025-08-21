"""Core job management utilities for the Rotterdam server."""

from __future__ import annotations

import time
from threading import Thread
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, field_validator

import reporting


class JobRequest(BaseModel):
    """Request body for a job submission."""

    serial: str
    static_metrics: Dict[str, float] | None = None
    dynamic_metrics: Dict[str, float] | None = None
    params: Dict[str, Any] | None = None

    @field_validator("static_metrics", "dynamic_metrics")
    @classmethod
    def _check_metrics(cls, v: Dict[str, float] | None) -> Dict[str, float] | None:
        """Ensure all metric values are non-negative numbers."""
        if v is None:
            return v
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"metric {key} must be numeric")
            if value < 0:
                raise ValueError(f"metric {key} must be non-negative")
        return v


# In-memory job store
_jobs: Dict[str, Dict[str, Any]] = {}


def _process_job(job_id: str, req: JobRequest) -> None:
    """Simulate job processing and populate the report."""
    time.sleep(0.5)
    risk = reporting.generate("unknown", req.static_metrics, req.dynamic_metrics)
    _jobs[job_id]["report"] = {
        "status": "completed",
        "risk": risk,
        "params": req.params or {},
    }


def submit_job(req: JobRequest) -> str:
    """Create a job and start background processing."""
    job_id = str(uuid4())
    _jobs[job_id] = {
        "request": req.model_dump(),
        "report": None,
        "created": time.time(),
    }
    Thread(target=_process_job, args=(job_id, req), daemon=True).start()
    return job_id


def list_jobs() -> list[Dict[str, Any]]:
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


def get_job(job_id: str) -> Dict[str, Any] | None:
    """Return details for a single job."""
    job = _jobs.get(job_id)
    if not job:
        return None
    return {
        "job_id": job_id,
        "status": "completed" if job["report"] else "pending",
        "created": job["created"],
        "request": job["request"],
    }


def delete_job(job_id: str) -> bool:
    """Remove a job and its report."""
    if job_id in _jobs:
        del _jobs[job_id]
        return True
    return False


def get_report(job_id: str) -> Dict[str, Any] | None:
    """Retrieve a report for a given job ID.

    Returns ``None`` if the job does not exist, otherwise the job identifier
    and report (which may be ``None`` while processing)."""
    job = _jobs.get(job_id)
    if not job:
        return None
    return {"job_id": job_id, "report": job["report"]}


def list_reports() -> list[Dict[str, Any]]:
    """Return all completed reports."""
    reports = []
    for jid, job in _jobs.items():
        if job["report"]:
            reports.append({"job_id": jid, **job["report"]})
    return reports


def get_analytics() -> Dict[str, Any]:
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


def get_device_analytics() -> list[Dict[str, Any]]:
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


def get_stats() -> Dict[str, int]:
    """Return counts of total and completed jobs."""
    total = len(_jobs)
    completed = sum(1 for j in _jobs.values() if j["report"])
    return {"jobs": total, "completed": completed}
