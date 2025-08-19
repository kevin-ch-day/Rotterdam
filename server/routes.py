"""API routes for submitting APK scans and retrieving results."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from orchestrator.scheduler import scheduler
from risk_reporting import create_risk_report
from storage.repository import RiskReportRepository

router = APIRouter()

# Repository instance to persist and retrieve risk reports
_repo = RiskReportRepository()

# Directory for analysis outputs and uploaded files
_ANALYSIS_ROOT = Path("analysis")
_ANALYSIS_ROOT.mkdir(exist_ok=True)


def _process_apk(apk_path: str) -> dict[str, str]:
    """Worker job to analyse ``apk_path`` and persist results.

    Returns a mapping with the package name and analysis directory used so that
    API endpoints can later retrieve reports.
    """
    path = Path(apk_path)
    package_name = path.stem

    # Generate a risk report and persist via the repository
    result = create_risk_report(package_name, repository=_repo)

    # Write JSON and HTML versions to a unique directory
    out_dir = _ANALYSIS_ROOT / uuid.uuid4().hex
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "report.json"
    json_path.write_text(json.dumps(result, indent=2))

    html_path = out_dir / "report.html"
    html_content = "<html><body><pre>{}</pre></body></html>".format(
        json.dumps(result, indent=2)
    )
    html_path.write_text(html_content)

    return {"package_name": package_name, "analysis_dir": str(out_dir)}


@router.post("/scans")
async def create_scan(file: UploadFile = File(...)) -> dict[str, str]:
    """Accept an APK upload and queue it for analysis."""
    uploads_dir = _ANALYSIS_ROOT / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    dest = uploads_dir / file.filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job_id = scheduler.submit_job(_process_apk, str(dest))
    return {"id": job_id}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str) -> dict[str, object]:
    """Return the status of a queued scan and any available risk report."""
    status = scheduler.job_status(scan_id)
    report: dict | None = None

    job = scheduler.get_job(scan_id)
    if status == "completed" and job and job.result:
        package = job.result.get("package_name")
        if package:
            latest = _repo.get_latest(package)
            report = latest.to_dict() if latest else None

    return {"id": scan_id, "status": status, "report": report}


@router.get("/scans/{scan_id}/report")
async def stream_report(scan_id: str, format: str = "json"):
    """Stream the JSON or HTML report file for a completed scan."""
    job = scheduler.get_job(scan_id)
    if not job or job.status != "completed" or not job.result:
        raise HTTPException(status_code=404, detail="report not available")

    analysis_dir = job.result.get("analysis_dir")
    if not analysis_dir:
        raise HTTPException(status_code=404, detail="report not available")

    path = Path(analysis_dir) / f"report.{format}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="report not found")

    media_type = "application/json" if format == "json" else "text/html"
    return FileResponse(path, media_type=media_type, filename=path.name)
