from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceInfo:
    """Metadata about a connected Android device."""

    serial: str = ""
    state: str = ""
    connection: str = ""
    type: str = ""
    manufacturer: str = ""
    model: str = ""
    android_release: str = ""
    sdk: str = ""
    abi: str = ""
    platform: str = ""
    hardware: str = ""
    build_tags: str = ""
    build_type: str = ""
    debuggable: str = ""
    secure: str = ""
    is_rooted: bool = False
    trust: str = ""
    product: str = ""
    device: str = ""
    transport_id: str = ""
    fingerprint_short: str = ""
