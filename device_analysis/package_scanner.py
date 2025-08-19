#!/usr/bin/env python3
"""Scan installed apps on a device for dangerous permissions."""

from __future__ import annotations

import subprocess
from typing import List, Dict, Any

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

# Common social media or high-value packages to flag during inventory
HIGH_VALUE_PACKAGES = {
    "com.twitter.android",
    "com.instagram.android",
    "com.facebook.katana",
    "com.facebook.orca",
    "com.whatsapp",
    "com.zhiliaoapp.musically",  # TikTok
    "com.ss.android.ugc.trill",   # TikTok alt package name
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


def inventory_packages(serial: str) -> List[Dict[str, Any]]:
    """Return detailed info for installed packages.

    Each dict contains:
        package: package name
        path: APK path on device
        installer: installer package name if available
        version_name, version_code: extracted from dumpsys
        high_value: whether package is in HIGH_VALUE_PACKAGES
    """

    adb = _adb_path()
    try:
        proc = _run_adb(
            [adb, "-s", serial, "shell", "pm", "list", "packages", "-f", "-i"],
            timeout=15,
        )
    except subprocess.CalledProcessError:
        return []

    packages: List[Dict[str, str]] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        line = line[len("package:") :]
        installer = ""
        if " installer=" in line:
            pkg_part, installer = line.split(" installer=", 1)
        else:
            pkg_part = line
        path = ""
        pkg = ""
        if "=" in pkg_part:
            path, pkg = pkg_part.split("=", 1)
        else:
            pkg = pkg_part
        info: Dict[str, str] = {
            "package": pkg,
            "path": path,
            "installer": installer,
            "version_name": "",
            "version_code": "",
            "high_value": pkg in HIGH_VALUE_PACKAGES,
        }

        # Fetch version details
        try:
            dump = _run_adb(
                [adb, "-s", serial, "shell", "dumpsys", "package", pkg], timeout=10
            )
            for ln in (dump.stdout or "").splitlines():
                ln = ln.strip()
                if ln.startswith("versionName="):
                    info["version_name"] = ln.split("=", 1)[1]
                elif ln.startswith("versionCode="):
                    info["version_code"] = ln.split("=", 1)[1].split()[0]
                if info["version_name"] and info["version_code"]:
                    break
        except subprocess.CalledProcessError:
            pass

        packages.append(info)

    return packages
