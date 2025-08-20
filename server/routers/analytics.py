"""Analytics endpoints for completed reports."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from server.job_service import get_analytics, get_device_analytics

router = APIRouter()


@router.get("/analytics")
async def analytics() -> Dict[str, Any]:
    """Compute simple analytics for completed reports."""
    return get_analytics()


@router.get("/analytics/devices")
async def device_analytics() -> list[Dict[str, Any]]:
    """Compute analytics grouped by device serial."""
    return get_device_analytics()
