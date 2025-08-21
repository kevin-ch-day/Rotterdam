"""Device enumeration endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from fastapi import APIRouter

from devices.service import discover, list_packages, props

router = APIRouter()


@router.get("/devices")
async def get_devices() -> list[Dict[str, Any]]:
    """Enumerate connected devices.

    If ADB or device discovery fails, return an empty list instead of raising
    so the API remains usable in environments without Android tools."""
    try:
        return [asdict(d) for d in discover()]
    except Exception:
        return []


@router.get("/devices/{serial}")
async def get_device(serial: str) -> Dict[str, Any]:
    """Return metadata for a single device."""
    try:
        return asdict(props(serial))
    except Exception:
        return {}


@router.get("/devices/{serial}/packages")
async def get_device_packages(serial: str) -> list[Dict[str, Any]]:
    """Return installed packages for the specified device."""
    try:
        return list_packages(serial)
    except Exception:
        return []
