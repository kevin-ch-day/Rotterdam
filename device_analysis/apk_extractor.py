#!/usr/bin/env python3
"""Utilities to pull APKs from a connected device."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .device_discovery import _adb_path, _run_adb


def pull_apk(serial: str, package: str, dest_dir: str = "output/apks") -> Path:
    """Pull the APK for ``package`` from the device ``serial``.

    Returns the local file path of the pulled APK.
    """
    adb = _adb_path()
    proc = _run_adb([adb, "-s", serial, "shell", "pm", "path", package], timeout=10)
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
    _run_adb([adb, "-s", serial, "pull", remote, str(dest)], timeout=60)
    return dest
