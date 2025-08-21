from __future__ import annotations

from typing import Any, Dict, List

from platform.android.devices import discovery as _discovery
from platform.android.devices import packages as _packages
from platform.android.devices import props as _props

from .types import DeviceInfo


def discover() -> List[DeviceInfo]:
    """Return connected devices enriched with metadata."""
    try:
        devices = _discovery.list_detailed_devices()
    except RuntimeError:
        return []
    return [DeviceInfo(**d) for d in devices]


def _props_to_info(serial: str, props: Dict[str, str]) -> DeviceInfo:
    rooted = _props._infer_root_status(props)
    return DeviceInfo(
        serial=serial,
        manufacturer=props.get("ro.product.manufacturer", ""),
        model=props.get("ro.product.model", ""),
        android_release=props.get("ro.build.version.release", ""),
        sdk=props.get("ro.build.version.sdk", ""),
        abi=props.get("ro.product.cpu.abi", ""),
        platform=props.get("ro.board.platform", ""),
        hardware=props.get("ro.hardware", ""),
        build_tags=props.get("ro.build.tags", ""),
        build_type=props.get("ro.build.type", ""),
        debuggable=props.get("ro.debuggable", ""),
        secure=props.get("ro.secure", ""),
        is_rooted=rooted,
        trust="low" if rooted else "high",
        product=props.get("ro.product.name", ""),
        device=props.get("ro.product.device", ""),
        fingerprint_short=_props._short_fingerprint(props.get("ro.build.fingerprint", "")),
    )


def props(serial: str) -> DeviceInfo:
    """Return metadata for the device with the given serial."""
    return _props_to_info(serial, _props.get_props(serial))


def list_packages(serial: str) -> List[Dict[str, Any]]:
    """Return package inventory for the specified device."""
    return _packages.inventory_packages(serial)
