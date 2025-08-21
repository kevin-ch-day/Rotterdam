#!/usr/bin/env python3
# File: platform/android/devices/packages.py
"""Scan installed apps on a device for dangerous permissions."""

from __future__ import annotations

import subprocess
from typing import Any, Dict, List, Set

from .adb import _run_adb

# A small, non-exhaustive set of permissions considered risky for demos.
DANGEROUS_PERMISSIONS: Set[str] = {
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
HIGH_VALUE_PACKAGES: Set[str] = {
    "com.twitter.android",
    "com.instagram.android",
    "com.facebook.katana",
    "com.facebook.orca",
    "com.whatsapp",
    "com.zhiliaoapp.musically",  # TikTok
    "com.ss.android.ugc.trill",  # TikTok alt package name
}

# Hardcoded mapping of known packages to categories.  These lists are intentionally
# small and primarily serve as examples for how categorisation could work.  The
# structure makes it easy to later replace with a JSON or database driven
# configuration.
APP_CATEGORIES: Dict[str, Set[str]] = {
    "Social Media": {
        "com.twitter.android",
        "com.instagram.android",
        "com.facebook.katana",
        "com.zhiliaoapp.musically",
        "com.ss.android.ugc.trill",
    },
    "Messaging": {
        "com.whatsapp",
        "com.facebook.orca",
    },
    "Financial": {
        "com.paypal.android.p2pmobile",
        "com.chase.sig.android",
    },
}


def list_installed_packages(serial: str) -> List[str]:
    """Return package names installed on the given device."""
    try:
        proc = _run_adb(["-s", serial, "shell", "pm", "list", "packages"], timeout=10)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to list packages on device {serial}: {exc}") from exc

    packages: List[str] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line.split(":", 1)[1])
    return packages


def _get_permissions(serial: str, package: str) -> List[str]:
    """Return permissions declared by the package."""
    try:
        proc = _run_adb(["-s", serial, "shell", "dumpsys", "package", package], timeout=10)
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


def _categorize_package(pkg: str) -> List[str]:
    """Return a list of categories that the package is known to belong to."""
    cats: List[str] = []
    for category, names in APP_CATEGORIES.items():
        if pkg in names:
            cats.append(category)
    return cats


def scan_for_dangerous_permissions(serial: str) -> List[Dict[str, Any]]:
    """Return packages that request permissions in ``DANGEROUS_PERMISSIONS``.

    Each result includes the package name, matched permissions, categories and a
    naive risk score based on the number of dangerous permissions requested.
    """

    results: List[Dict[str, Any]] = []
    packages = list_installed_packages(serial)
    for pkg in packages:
        perms = _get_permissions(serial, pkg)
        risky = sorted(p for p in perms if p in DANGEROUS_PERMISSIONS)
        if risky:
            categories = _categorize_package(pkg)
            risk = len(risky) + (1 if pkg in HIGH_VALUE_PACKAGES else 0)
            results.append(
                {
                    "package": pkg,
                    "permissions": risky,
                    "risk_score": risk,
                    "categories": categories,
                }
            )
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

    try:
        proc = _run_adb(
            ["-s", serial, "shell", "pm", "list", "packages", "-f", "-i"],
            timeout=15,
        )
    except subprocess.CalledProcessError:
        return []

    packages: List[Dict[str, Any]] = []
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
        system_app = bool(path) and not path.startswith("/data/")
        priv_app = "/priv-app/" in path
        info: Dict[str, Any] = {
            "package": pkg,
            "path": path,
            "installer": installer,
            "version_name": "",
            "version_code": "",
            "high_value": pkg in HIGH_VALUE_PACKAGES,
            "uid": "",
            "system": system_app,
            "priv": priv_app,
            "dangerous_permissions": [],
            "risk_score": 0,
            "categories": _categorize_package(pkg),
        }

        # Fetch version details and additional metadata
        try:
            dump = _run_adb(["-s", serial, "shell", "dumpsys", "package", pkg], timeout=10)
            for ln in (dump.stdout or "").splitlines():
                ln = ln.strip()
                if ln.startswith("versionName="):
                    info["version_name"] = ln.split("=", 1)[1]
                elif ln.startswith("versionCode="):
                    info["version_code"] = ln.split("=", 1)[1].split()[0]
                elif ln.startswith("userId=") or ln.startswith("uid="):
                    info["uid"] = ln.split("=", 1)[1].split()[0]
                elif ln.startswith("pkgFlags=") or ln.startswith("flags="):
                    flags = ln.split("[", 1)[-1].split("]", 1)[0].replace(",", " ")
                    if "SYSTEM" in flags:
                        info["system"] = True
                    if "PRIVILEGED" in flags:
                        info["priv"] = True
                elif ln.startswith("uses-permission:"):
                    perm = ln.split(":", 1)[1].strip()
                    if perm:
                        info.setdefault("permissions", []).append(perm)
                        if perm in DANGEROUS_PERMISSIONS:
                            info["dangerous_permissions"].append(perm)
            # Calculate risk score once permissions gathered
            info["risk_score"] = len(info["dangerous_permissions"]) + (
                1 if info["high_value"] else 0
            )
        except subprocess.CalledProcessError:
            pass

        packages.append(info)

    return packages
