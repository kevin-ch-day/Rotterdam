#!/usr/bin/env python3
# File: android/devices/apk.py
"""Utilities to pull APKs from a connected device."""

from __future__ import annotations

from pathlib import Path
import hashlib
import getpass
from datetime import datetime
from typing import Dict

from android.adb import run as _run_adb


def pull_apk(serial: str, package: str, dest_dir: str = "output/apks") -> Path:
    """Pull the APK for ``package`` from the device ``serial``.

    Returns the local file path of the pulled APK.
    """
    proc = _run_adb(["-s", serial, "shell", "pm", "path", package], timeout=10)
    remote = ""
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            remote = line.split(":", 1)[1]
            break
    if not remote:
        raise RuntimeError(f"Package {package} not found on device")

    dest_folder = Path(dest_dir)
    dest_folder.mkdir(parents=True, exist_ok=True)
    dest = dest_folder / f"{package}.apk"
    _run_adb(["-s", serial, "pull", remote, str(dest)], timeout=60)
    return dest


def acquire_apk(
    serial: str,
    package: str,
    dest_dir: str = "output/apks",
    operator: str | None = None,
) -> Dict[str, str]:
    """Pull an APK and record chain-of-custody metadata.

    Returns a dictionary with artifact path, SHA-256 hash, timestamp, operator,
    and source device/package identifiers.
    """

    path = pull_apk(serial, package, dest_dir=dest_dir)
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    if operator is None:
        operator = getpass.getuser()
    return {
        "artifact": str(path),
        "sha256": sha256,
        "timestamp": timestamp,
        "operator": operator,
        "device": serial,
        "package": package,
    }
