#!/usr/bin/env python3
# File: platform/android/devices/discovery.py
# discovery.py
"""Helpers for discovering and enriching connected Android devices via ADB."""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from .adb import _adb_path, _run_adb
from .props import (
    get_props,
    _infer_connection_kind,
    _infer_is_emulator,
    _infer_root_status,
    _short_fingerprint,
)
from utils.logging_utils.logging_config import get_logger


logger = get_logger(__name__)


# -----------------------------
# Top-level: raw check
# -----------------------------

def check_connected_devices() -> str:
    """Run `adb devices -l` and return the raw stdout."""
    adb = _adb_path()
    logger.info("checking connected devices", extra={"adb": adb})
    try:
        result = _run_adb([adb, "devices", "-l"])
    except PermissionError as e:
        logger.exception("adb not executable")
        raise RuntimeError(
            f"adb at '{adb}' is not executable (Permission denied). "
            "Fix perms/SELinux or use system 'adb' (dnf install android-tools)."
        ) from e
    except FileNotFoundError as e:
        logger.exception("adb not found")
        raise RuntimeError(
            "adb not found. Install platform-tools or `dnf install android-tools`, and ensure it's on PATH."
        ) from e
    except subprocess.CalledProcessError:
        logger.warning("initial adb devices failed; restarting adb server")
        try:
            _run_adb([adb, "kill-server"])
            _run_adb([adb, "start-server"])
            result = _run_adb([adb, "devices", "-l"])
        except subprocess.CalledProcessError as e:
            logger.exception("error running adb after restart")
            raise RuntimeError(f"Error running adb: {e}") from e

    output = (result.stdout or "").strip()
    if not parse_devices_l(output):
        print("No Android devices detected.")
        print("Fedora users may need a udev rule such as:")
        print('  SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"')
        print(
            "SELinux may also need adjustment. See ANDROID_ANALYSIS_SETUP.md for details."
        )
    logger.info("adb devices output received")
    return output


# -----------------------------
# Parse `adb devices -l` output
# -----------------------------

def parse_devices_l(output: str) -> List[Dict[str, str]]:
    """Parse `adb devices -l` into a list of dicts."""
    lines = [ln.strip() for ln in (output or "").splitlines() if ln.strip()]
    if not lines:
        logger.info("no devices in adb output")
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
    logger.info("parsed %d devices", len(devices))
    return devices


# -----------------------------
# Public: list detailed devices
# -----------------------------

def list_detailed_devices() -> List[Dict[str, Any]]:
    """Return a list of enriched device dicts for display/selection."""
    logger.info("list_detailed_devices")
    raw = check_connected_devices()
    base = parse_devices_l(raw)

    serials = [d["serial"] for d in base if d.get("state", "").lower() == "device"]
    props_map: Dict[str, Dict[str, str]] = {}
    if serials:
        def _fetch(serial: str) -> tuple[str, Dict[str, str]]:
            return serial, get_props(serial)

        with ThreadPoolExecutor(max_workers=min(8, len(serials))) as ex:
            for serial, props in ex.map(_fetch, serials):
                props_map[serial] = props

    detailed: List[Dict[str, Any]] = []
    for d in base:
        serial = d.get("serial", "")
        state = (d.get("state") or "").lower()
        props = props_map.get(serial, {})

        info: Dict[str, Any] = {
            "serial": serial,
            "state": state,
            "connection": _infer_connection_kind(serial, d),
            "type": "unknown",
            "manufacturer": "",
            "model": "",
            "android_release": "",
            "sdk": "",
            "abi": "",
            "platform": "",
            "hardware": "",
            "build_tags": "",
            "build_type": "",
            "debuggable": "",
            "secure": "",
            "is_rooted": False,
            "trust": "unknown",
            "product": d.get("product", ""),
            "device": d.get("device", ""),
            "transport_id": d.get("transport_id", d.get("transport", "")),
            "fingerprint_short": "",
        }

        if state == "device":
            info["manufacturer"] = props.get("ro.product.manufacturer", "")
            info["model"] = props.get("ro.product.model", "")
            info["android_release"] = props.get("ro.build.version.release", "")
            info["sdk"] = props.get("ro.build.version.sdk", "")
            info["abi"] = props.get("ro.product.cpu.abi", "")
            info["platform"] = props.get("ro.board.platform", "")
            info["hardware"] = props.get("ro.hardware", "")
            info["build_tags"] = props.get("ro.build.tags", "")
            info["build_type"] = props.get("ro.build.type", "")
            info["debuggable"] = props.get("ro.debuggable", "")
            info["secure"] = props.get("ro.secure", "")
            fp = props.get("ro.build.fingerprint", "")
            info["fingerprint_short"] = _short_fingerprint(fp)
            info["type"] = "emulator" if _infer_is_emulator(serial, props, d) else "physical"
            rooted = _infer_root_status(props)
            info["is_rooted"] = rooted
            info["trust"] = "low" if rooted else "high"
        else:
            info["type"] = "unknown"

        detailed.append(info)

    return detailed
