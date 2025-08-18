#!/usr/bin/env python3
"""Scan installed apps on a device for dangerous permissions."""

from __future__ import annotations

import subprocess
from typing import List, Dict

from device_analysis.device_discovery import _adb_path, _run_adb

# A small, non-exhaustive set of permissions considered risky for demos.
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.SEND_SMS",
    "android.permission.READ_PHONE_STATE",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.SYSTEM_ALERT_WINDOW",
}


def list_installed_packages(serial: str) -> List[str]:
    """Return package names installed on the given device."""
    adb = _adb_path()
    try:
        proc = _run_adb([adb, "-s", serial, "shell", "pm", "list", "packages"], timeout=10)
    except subprocess.CalledProcessError:
        return []

    packages: List[str] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line.split(":", 1)[1])
    return packages


def _get_permissions(serial: str, package: str) -> List[str]:
    """Return permissions declared by the package."""
    adb = _adb_path()
    try:
        proc = _run_adb([adb, "-s", serial, "shell", "dumpsys", "package", package], timeout=10)
    except subprocess.CalledProcessError:
        return []

    perms: List[str] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("uses-permission:"):
            perm = line.split(":", 1)[1].strip()
            if perm:
                perms.append(perm)
    return perms


def scan_for_dangerous_permissions(serial: str) -> List[Dict[str, List[str]]]:
    """Return packages that request permissions in DANGEROUS_PERMISSIONS."""
    results: List[Dict[str, List[str]]] = []
    packages = list_installed_packages(serial)
    for pkg in packages:
        perms = _get_permissions(serial, pkg)
        risky = sorted(p for p in perms if p in DANGEROUS_PERMISSIONS)
        if risky:
            results.append({"package": pkg, "permissions": risky})
    return results
