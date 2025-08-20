"""Job submission and management endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Response

from server.job_service import (
    JobRequest,
    delete_job,
    get_job,
    list_jobs,
    submit_job,
)

router = APIRouter()


@router.post("/jobs")
async def create_job(req: JobRequest) -> Dict[str, str]:
    """Submit a job for processing and return a job ID."""
    job_id = submit_job(req)
    return {"job_id": job_id}


@router.get("/jobs")
async def get_jobs() -> list[Dict[str, Any]]:
    """Return all submitted jobs with their status."""
    return list_jobs()


@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: str) -> Dict[str, Any]:
    """Return details for a single job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def remove_job(job_id: str) -> Response:
    """Remove a job and its report."""
    if not delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return Response(status_code=204)
