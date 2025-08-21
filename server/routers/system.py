# server/routers/system.py
"""Hidden system-level endpoints for diagnostics."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app_config import app_config
from server.job_service import get_stats

router = APIRouter()

_start_monotonic = time.monotonic()


@router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    """Public liveness check exposing app metadata."""
    return {
        "status": "ok",
        "name": app_config.APP_NAME,
        "version": app_config.APP_VERSION,
    }


@router.get("/_healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Legacy liveness endpoint (deprecated)."""
    return await health()


@router.get("/_ready", include_in_schema=False)
async def ready() -> dict[str, bool]:
    """Readiness probe (add lightweight dependency checks here if needed)."""
    return {"ready": True}


@router.get("/about", include_in_schema=False)
async def about() -> dict[str, str]:
    """Return application metadata."""
    return {
        "name": app_config.APP_NAME,
        "version": app_config.APP_VERSION,
        "vendor": app_config.APP_VENDOR,
        "homepage": app_config.APP_HOMEPAGE,
    }


@router.get("/_stats", include_in_schema=False)
async def stats() -> dict[str, float | int]:
    """Internal statistics about the server."""
    uptime = time.monotonic() - _start_monotonic
    return {"uptime": uptime, **get_stats()}
