#!/usr/bin/env python3
# File: platform/android/devices/props.py
"""Helpers for retrieving and interpreting device properties."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict

from .adb import _run_adb
from core.errors import log_exception


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
    "ro.build.tags",
    "ro.build.type",
    "ro.debuggable",
    "ro.secure",
]


def _shell_getprops(serial: str, keys: list[str]) -> Dict[str, str]:
    """Fetch multiple getprop keys in one shell call and return a mapping."""
    lines = [f'echo "{k}=$(getprop {k})"' for k in keys]
    cmd = " ; ".join(lines)
    try:
        proc = _run_adb(["-s", serial, "shell", cmd], timeout=6)
        out = proc.stdout or ""
    except Exception as exc:
        log_exception("Failed to retrieve device properties", exc)
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


@lru_cache(maxsize=32)
def _cached_props(serial: str) -> Dict[str, str]:
    """Return cached property map for a device serial."""
    return _shell_getprops(serial, _PROP_KEYS)


def get_props(serial: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return cached properties for the given serial."""
    props = _cached_props(serial)
    if not keys or keys is _PROP_KEYS:
        return props
    return {k: props.get(k, "") for k in keys}


def _infer_connection_kind(serial: str, meta: Dict[str, str]) -> str:
    """Best-effort guess of USB vs TCPIP connection."""
    if "usb" in meta:
        return "USB"
    if ":" in serial and all(ch.isdigit() or ch == "." for ch in serial.split(":")[0]):
        return "TCPIP"
    return "UNKNOWN"


def _infer_is_emulator(serial: str, props: Dict[str, str], meta: Dict[str, str]) -> bool:
    """Return True if heuristics indicate the device is an emulator."""
    if serial.startswith("emulator-"):
        return True
    if props.get("ro.boot.qemu") == "1":
        return True
    manuf = (props.get("ro.product.manufacturer") or "").lower()
    if manuf in {"genymotion", "unknown", "goldfish", "google"}:
        fp = (props.get("ro.build.fingerprint") or "").lower()
        if "generic" in fp or "ranchu" in fp or "goldfish" in fp:
            return True
    if _infer_connection_kind(serial, meta) == "TCPIP":
        fp = (props.get("ro.build.fingerprint") or "").lower()
        if "generic" in fp or "sdk" in fp:
            return True
    return False


def _infer_root_status(props: Dict[str, str]) -> bool:
    """Best-effort check for signs of a rooted or developer build."""
    if props.get("ro.secure") == "0":
        return True
    if props.get("ro.debuggable") == "1":
        return True
    tags = (props.get("ro.build.tags") or "").lower()
    if "test-keys" in tags:
        return True
    build_type = props.get("ro.build.type", "")
    if build_type in {"eng", "userdebug"}:
        return True
    return False


def _short_fingerprint(fp: str, maxlen: int = 48) -> str:
    if not fp:
        return ""
    if len(fp) <= maxlen:
        return fp
    return fp[: maxlen - 1] + "…"
