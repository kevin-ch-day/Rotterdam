"""Device enumeration endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from devices.discovery import list_detailed_devices

router = APIRouter()


@router.get("/devices")
async def get_devices() -> list[Dict[str, Any]]:
    """Enumerate connected devices.

    If ADB or device discovery fails, return an empty list instead of raising
    so the API remains usable in environments without Android tools."""
    try:
        return list_detailed_devices()
    except Exception:
        return []
