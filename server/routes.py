"""API routes for submitting APK scans and retrieving results."""

# NOTE: Static files must reside under ``/ui/...`` so the server can mount them
# consistently. See ``server/main.py`` for the associated mount points.

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
import hashlib

from fastapi import APIRouter, File, HTTPException, UploadFile, Response, status
from fastapi.responses import FileResponse

from orchestrator.scheduler import scheduler
from reports.risk_reporting import create_risk_report
from storage.repository import ping_db

router = APIRouter()


@router.get("/health/db")
def health_db():
    ok, info, ms = ping_db()
    if ok:
        return {"status": "ok", "version": info, "latency_ms": round(ms, 1)}
    return Response(
        content=f'{{"status":"fail","error":{info!r},"latency_ms":{round(ms,1)}}}',
        media_type="application/json",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

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

    # Generate a risk report
    result = create_risk_report(package_name)

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

    # Derive findings from the risk breakdown for demonstration purposes
    findings = [
        {
            "id": key,
            "severity": "Low",
            "title": key.replace("_", " ").title(),
            "tags": [],
            "evidence": str(value),
        }
        for key, value in result.get("breakdown", {}).items()
    ]
    (out_dir / "findings.json").write_text(json.dumps(findings, indent=2))

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "package_name": package_name,
        "analysis_dir": str(out_dir),
        "sha256": sha256,
        "score": result.get("score"),
        "created_at": time.time(),
    }


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/scans")
async def create_scan(file: UploadFile = File(...)) -> dict[str, str]:
    """Accept an APK upload and queue it for analysis.

    Files larger than ``MAX_UPLOAD_SIZE`` bytes are rejected to avoid resource
    exhaustion attacks."""
    uploads_dir = _ANALYSIS_ROOT / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    dest = uploads_dir / f"{uuid.uuid4().hex}_{safe_name}"

    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="file too large")
    dest.write_bytes(data)

    job_id = scheduler.submit_job(_process_apk, str(dest))
    return {"scan_id": job_id}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str) -> dict[str, object]:
    """Return the status of a queued scan and any available risk report."""
    status = scheduler.job_status(scan_id)
    report: dict | None = None

    job = scheduler.get_job(scan_id)
    if status == "completed" and job and job.result:
        analysis_dir = job.result.get("analysis_dir")
        if analysis_dir:
            report_path = Path(analysis_dir) / "report.json"
            if report_path.exists():
                report = json.loads(report_path.read_text())

    info: dict[str, object] = {"scan_id": scan_id, "status": status, "report": report}
    if job and job.result:
        info.update(
            {
                "pkg": job.result.get("package_name"),
                "sha256": job.result.get("sha256"),
                "score": job.result.get("score"),
                "started": job.created_at,
            }
        )
    return info


@router.get("/scans/{scan_id}/report")
async def stream_report(scan_id: str, format: str = "json"):
    """Stream the JSON or HTML report file for a completed scan."""
    job = scheduler.get_job(scan_id)
    if not job or job.status != "completed" or not job.result:
        raise HTTPException(status_code=404, detail="report not available")

    analysis_dir = job.result.get("analysis_dir")
    if not analysis_dir:
        raise HTTPException(status_code=404, detail="report not available")

    if format not in {"json", "html"}:
        raise HTTPException(status_code=400, detail="invalid format")

    path = Path(analysis_dir) / f"report.{format}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="report not found")

    media_type = "application/json" if format == "json" else "text/html"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/scans")
async def list_scans(limit: int = 50) -> list[dict[str, object]]:
    """Return recent scans and their status."""
    jobs = scheduler.list_jobs()
    items: list[dict[str, object]] = []
    for scan_id, status in jobs.items():
        job = scheduler.get_job(scan_id)
        info: dict[str, object] = {"scan_id": scan_id, "status": status}
        if job and job.result:
            info.update(
                {
                    "pkg": job.result.get("package_name"),
                    "sha256": job.result.get("sha256"),
                    "score": job.result.get("score"),
                    "started": job.created_at,
                }
            )
        items.append(info)
    return items[:limit]


@router.get("/scans/{scan_id}/findings")
async def get_findings(scan_id: str) -> list[dict[str, object]]:
    """Return findings for a completed scan."""
    job = scheduler.get_job(scan_id)
    if not job or job.status != "completed" or not job.result:
        raise HTTPException(status_code=404, detail="findings not available")
    analysis_dir = job.result.get("analysis_dir")
    path = Path(analysis_dir) / "findings.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="findings not found")
    return json.loads(path.read_text())


@router.get("/scans/{scan_id}/artifacts")
async def list_artifacts(scan_id: str) -> list[dict[str, str]]:
    """List downloadable artifacts for a completed scan."""
    job = scheduler.get_job(scan_id)
    if not job or job.status != "completed" or not job.result:
        raise HTTPException(status_code=404, detail="artifacts not available")
    analysis_dir = job.result.get("analysis_dir")
    artifacts = []
    for fmt in ("json", "html"):
        path = Path(analysis_dir) / f"report.{fmt}"
        if path.exists():
            artifacts.append(
                {"name": path.name, "url": f"/scans/{scan_id}/report?format={fmt}"}
            )
    return artifacts
