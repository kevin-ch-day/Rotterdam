from __future__ import annotations

from typing import Dict, List


def parse_devices_l(output: str) -> List[Dict[str, str]]:
    """Parse `adb devices -l` output into a list of dicts."""
    lines = [ln.strip() for ln in (output or "").splitlines() if ln.strip()]
    if not lines:
        return []
    if lines[0].lower().startswith("list of devices"):
        lines = lines[1:]
    devices: List[Dict[str, str]] = []
    for ln in lines:
        parts = ln.split()
        if not parts:
            continue
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"
        meta: Dict[str, str] = {}
        for p in parts[2:]:
            if ":" in p:
                k, v = p.split(":", 1)
                meta[k] = v
        devices.append({"serial": serial, "state": state, **meta})
    return devices

__all__ = ["parse_devices_l"]
