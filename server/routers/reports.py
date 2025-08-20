"""Report retrieval endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from server.job_service import get_report, list_reports

router = APIRouter()


@router.get("/reports/{job_id}")
async def fetch_report(job_id: str) -> Dict[str, Any]:
    """Retrieve a report for a given job ID."""
    report = get_report(job_id)
    if report is None:
        # Distinguish between missing job and pending report
        raise HTTPException(status_code=404, detail="Job not found")
    if report["report"] is None:
        return JSONResponse(status_code=202, content={"status": "pending"})
    return report


@router.get("/reports")
async def fetch_reports() -> list[Dict[str, Any]]:
    """Return all completed reports."""
    return list_reports()
