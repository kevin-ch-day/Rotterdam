#!/usr/bin/env python3
# device_analysis/device_discovery.py
"""
Helpers for discovering and enriching connected Android devices via ADB.
"""

from __future__ import annotations
import shutil
import subprocess
from typing import List, Dict, Any
from app_utils import app_config


# -----------------------------
# Low-level ADB runners
# -----------------------------

def _run_adb(args: list[str], *, timeout: int = 8) -> subprocess.CompletedProcess:
    """
    Run adb with robust defaults. Raises FileNotFoundError, CalledProcessError, PermissionError as-is.
    """
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout)


def _adb_path() -> str:
    # Prefer executable SDK adb, else PATH adb, else the SDK candidate
    path = app_config.get_adb_path()
    which = shutil.which("adb")
    # If our chosen path is not executable but PATH has one, prefer PATH
    try:
        # quick, non-raising probe
        subprocess.run([path, "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return path
    except Exception:
        return which or path


# -----------------------------
# Top-level: raw check
# -----------------------------

def check_connected_devices() -> str:
    """
    Run `adb devices -l` and return the raw stdout.
    Raises RuntimeError with a friendly message on failure.
    """
    adb = _adb_path()
    try:
        result = _run_adb([adb, "devices", "-l"])
    except PermissionError as e:
        raise RuntimeError(
            f"adb at '{adb}' is not executable (Permission denied). "
            "Fix perms/SELinux or use system 'adb' (dnf install android-tools)."
        ) from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "adb not found. Install platform-tools or `dnf install android-tools`, and ensure it's on PATH."
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running adb: {e}") from e

    return (result.stdout or "").strip()


# -----------------------------
# Parse `adb devices -l` output
# -----------------------------

def parse_devices_l(output: str) -> List[Dict[str, str]]:
    """
    Parse `adb devices -l` into a list of dicts with keys:
      serial, state, product, model, device, transport_id, usb, (any other key:value tokens present)
    """
    lines = [ln.strip() for ln in (output or "").splitlines() if ln.strip()]
    if not lines:
        return []

    # Drop header if present
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


# -----------------------------
# Enrichment helpers
# -----------------------------

_PROP_KEYS = [
    "ro.product.manufacturer",
    "ro.product.model",
    "ro.build.version.release",
    "ro.build.version.sdk",
    "ro.product.cpu.abi",
    "ro.board.platform",
    "ro.hardware",
    "ro.boot.qemu",
    "ro.build.fingerprint",
    # Properties useful for basic trust / rooting heuristics
    "ro.build.tags",
    "ro.build.type",
    "ro.debuggable",
    "ro.secure",
]

def _shell_getprops(serial: str, keys: list[str]) -> Dict[str, str]:
    """
    Fetch multiple getprop keys in one shell call (faster than N calls).
    Returns a dict {key: value}. Missing keys -> ''.
    """
    adb = _adb_path()
    # Build a single command that echoes key=value lines
    lines = []
    for k in keys:
        # Quote the key and produce "key=value" lines
        lines.append(f'echo "{k}=$(getprop {k})"')
    cmd = " ; ".join(lines)
    try:
        proc = _run_adb([adb, "-s", serial, "shell", cmd], timeout=6)
        out = proc.stdout or ""
    except Exception:
        return {k: "" for k in keys}

    result: Dict[str, str] = {k: "" for k in keys}
    for ln in out.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k in result:
                result[k] = v
    return result


def _infer_connection_kind(serial: str, meta: Dict[str, str]) -> str:
    """
    Try to infer whether connection is USB or TCP/IP.
    - presence of meta['usb'] usually means USB (e.g., 'usb:1-13')
    - serial like '192.168.1.5:5555' implies TCP/IP
    """
    if "usb" in meta:
        return "USB"
    if ":" in serial and all(ch.isdigit() or ch == "." for ch in serial.split(":")[0]):
        return "TCPIP"
    return "UNKNOWN"


def _infer_is_emulator(serial: str, props: Dict[str, str], meta: Dict[str, str]) -> bool:
    """
    Heuristics to detect emulator:
    - serial starts with 'emulator-'
    - ro.boot.qemu == '1'
    - manufacturer strings commonly used by emulators (best-effort)
    """
    if serial.startswith("emulator-"):
        return True
    if props.get("ro.boot.qemu") == "1":
        return True
    manuf = (props.get("ro.product.manufacturer") or "").lower()
    if manuf in {"genymotion", "unknown", "goldfish", "google"}:
        # goldfish/ranchu are AOSP emulator hw
        fp = (props.get("ro.build.fingerprint") or "").lower()
        if "generic" in fp or "ranchu" in fp or "goldfish" in fp:
            return True
    # If it lacks USB info and looks like TCP/IP + generic fingerprint, treat as emulator
    if _infer_connection_kind(serial, meta) == "TCPIP":
        fp = (props.get("ro.build.fingerprint") or "").lower()
        if "generic" in fp or "sdk" in fp:
            return True
    return False


def _infer_root_status(props: Dict[str, str]) -> bool:
    """Best-effort check for signs of a rooted or developer build."""
    # ro.secure=0 indicates a non-secure build
    if props.get("ro.secure") == "0":
        return True
    # ro.debuggable=1 allows adb shell with root-like capabilities
    if props.get("ro.debuggable") == "1":
        return True
    # test-keys in build tags often means an engineering build
    tags = (props.get("ro.build.tags") or "").lower()
    if "test-keys" in tags:
        return True
    # eng/userdebug builds are typically non-production
    build_type = props.get("ro.build.type", "")
    if build_type in {"eng", "userdebug"}:
        return True
    return False


def _short_fingerprint(fp: str, maxlen: int = 48) -> str:
    if not fp:
        return ""
    if len(fp) <= maxlen:
        return fp
    return fp[:maxlen - 1] + "…"


# -----------------------------
# Public: list detailed devices
# -----------------------------

def list_detailed_devices() -> List[Dict[str, Any]]:
    """
    Returns a list of enriched device dicts for display/selection.
    Each item has:
      - serial, state
      - connection: USB|TCPIP|UNKNOWN
      - type: physical|emulator|unknown
      - manufacturer, model
      - android_release, sdk
      - abi, platform, hardware
      - product, device (from -l)
      - fingerprint_short
      - build_tags, build_type, debuggable, secure
      - is_rooted and a simple trust classification
    """
    raw = check_connected_devices()
    base = parse_devices_l(raw)

    detailed: List[Dict[str, str]] = []
    for d in base:
        serial = d.get("serial", "")
        state = (d.get("state") or "").lower()

        # Default augmented fields
        info: Dict[str, str] = {
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

        # Only query props when the device is fully online
        if state == "device":
            props = _shell_getprops(serial, _PROP_KEYS)
            info["manufacturer"]   = props.get("ro.product.manufacturer", "")
            info["model"]          = props.get("ro.product.model", "")
            info["android_release"]= props.get("ro.build.version.release", "")
            info["sdk"]            = props.get("ro.build.version.sdk", "")
            info["abi"]            = props.get("ro.product.cpu.abi", "")
            info["platform"]       = props.get("ro.board.platform", "")
            info["hardware"]       = props.get("ro.hardware", "")
            info["build_tags"]     = props.get("ro.build.tags", "")
            info["build_type"]     = props.get("ro.build.type", "")
            info["debuggable"]     = props.get("ro.debuggable", "")
            info["secure"]         = props.get("ro.secure", "")
            fp                     = props.get("ro.build.fingerprint", "")
            info["fingerprint_short"] = _short_fingerprint(fp)
            info["type"] = "emulator" if _infer_is_emulator(serial, props, d) else "physical"
            rooted = _infer_root_status(props)
            info["is_rooted"] = rooted
            info["trust"] = "low" if rooted else "high"
        else:
            # unauthorized / offline / recovery / sideload etc. → skip props
            info["type"] = "unknown"

        detailed.append(info)

    return detailed
