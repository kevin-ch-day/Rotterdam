# server/routers/system.py
"""Hidden system-level endpoints for diagnostics."""

from __future__ import annotations

import time
from fastapi import APIRouter

from server.job_service import get_stats

router = APIRouter()

_start_monotonic = time.monotonic()


@router.get("/_healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Cheap liveness check used by tests and orchestration."""
    return {"status": "ok"}


@router.get("/_ready", include_in_schema=False)
async def ready() -> dict[str, bool]:
    """Readiness probe (add lightweight dependency checks here if needed)."""
    return {"ready": True}


@router.get("/_stats", include_in_schema=False)
async def stats() -> dict[str, float | int]:
    """Internal statistics about the server."""
    uptime = time.monotonic() - _start_monotonic
    return {"uptime": uptime, **get_stats()}
