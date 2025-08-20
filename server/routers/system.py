"""Hidden system-level endpoints for diagnostics."""

from __future__ import annotations

import time
from fastapi import APIRouter

from server.job_service import get_stats

router = APIRouter()

_start_time = time.time()


@router.get("/_healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Simple liveness check."""
    return {"status": "ok"}


@router.get("/_ready", include_in_schema=False)
async def ready() -> dict[str, str]:
    """Simple readiness check."""
    return {"status": "ok"}

@router.get("/_stats", include_in_schema=False)
async def stats() -> dict[str, float | int]:
    """Internal statistics about the server."""
    uptime = time.time() - _start_time
    return {"uptime": uptime, **get_stats()}
