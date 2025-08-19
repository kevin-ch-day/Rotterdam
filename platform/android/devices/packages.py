#!/usr/bin/env python3
"""Utilities for enumerating packages and their runtime permissions."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .adb import _adb_path, _run_adb

# ---------------------------------------------------------------------------
# Permission categorisation
# ---------------------------------------------------------------------------

# A small, non-exhaustive set of permissions considered dangerous for demos.
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
}

# Signature-level permissions typically reserved for the OS or OEM apps.
SIGNATURE_PERMISSIONS = {
    "android.permission.READ_PRIVILEGED_PHONE_STATE",
    "android.permission.PACKAGE_USAGE_STATS",
}

# Special permissions granted via settings menus rather than standard prompts.
SPECIAL_PERMISSIONS = {
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.WRITE_SETTINGS",
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

# Mapping of specific permissions to higher-level risk flags
_RISK_FLAG_MAP = {
    "android.permission.INTERNET": "Internet",
    "android.permission.READ_CONTACTS": "Contacts",
    "android.permission.WRITE_CONTACTS": "Contacts",
    "android.permission.GET_ACCOUNTS": "Contacts",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "Background Location",
    "android.permission.RECEIVE_BOOT_COMPLETED": "Autostart",
    "android.permission.SYSTEM_ALERT_WINDOW": "Global Visibility",
    "android.permission.REQUEST_INSTALL_PACKAGES": "Installs APKs",
}


def _get_app_ops(serial: str, package: str) -> Dict[str, str]:
    """Return app-op modes for ``package`` using ``cmd appops``."""
    adb = _adb_path()
    try:
        proc = _run_adb(
            [adb, "-s", serial, "shell", "cmd", "appops", "get", package], timeout=10
        )
    except subprocess.CalledProcessError:
        return {}
    ops: Dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        op, rest = line.split(":", 1)
        op = op.strip()
        mode = rest.split()[0]
        ops[op] = mode
    return ops


def list_installed_packages(serial: str) -> List[str]:
    """Return package names installed on the given device."""
    adb = _adb_path()
    try:
        proc = _run_adb([adb, "-s", serial, "shell", "pm", "list", "packages"], timeout=10)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to list packages on device {serial}: {exc}") from exc

    packages: List[str] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line.split(":", 1)[1])
    return packages


def _get_permissions(serial: str, package: str) -> List[Dict[str, Any]]:
    """Return permissions declared by ``package`` with grant state and app op mode."""
    adb = _adb_path()
    try:
        proc = _run_adb([adb, "-s", serial, "shell", "dumpsys", "package", package], timeout=10)
    except subprocess.CalledProcessError:
        return []

    perms: Dict[str, Dict[str, Any]] = {}
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("uses-permission:"):
            perm = line.split(":", 1)[1].strip()
            if perm:
                perms.setdefault(perm, {"name": perm, "granted": False})
        elif ": granted=" in line:
            name, rest = line.split(": granted=", 1)
            granted = rest.split()[0].lower() == "true"
            name = name.strip()
            perms.setdefault(name, {"name": name})["granted"] = granted

    # Query runtime app-op modes (e.g. allow/deny/ignore)
    app_ops = _get_app_ops(serial, package)

    detailed: List[Dict[str, Any]] = []
    for perm in perms.values():
        name = perm["name"]
        if name in DANGEROUS_PERMISSIONS:
            category = "dangerous"
        elif name in SIGNATURE_PERMISSIONS:
            category = "signature"
        elif name in SPECIAL_PERMISSIONS:
            category = "special"
        else:
            category = "other"
        op_name = name.split(".")[-1]
        mode = app_ops.get(op_name, "")
        detailed.append(
            {
                "name": name,
                "granted": perm.get("granted", False),
                "category": category,
                **({"mode": mode} if mode else {}),
            }
        )
    return detailed


def _derive_risk_flags(perms: Iterable[str]) -> List[str]:
    """Return sorted list of high-level risk flags for ``perms``."""
    flags = {flag for p in perms if (flag := _RISK_FLAG_MAP.get(p))}
    return sorted(flags)


def scan_for_dangerous_permissions(serial: str) -> List[Dict[str, Any]]:
    """Return packages requesting risky permissions with categories and flags."""
    results: List[Dict[str, Any]] = []
    packages = list_installed_packages(serial)
    for pkg in packages:
        perms = _get_permissions(serial, pkg)
        risky = [p for p in perms if p["category"] in {"dangerous", "signature", "special"}]
        risk_flags = _derive_risk_flags(p["name"] for p in perms)
        if risky:
            results.append({"package": pkg, "permissions": risky, "risk_flags": risk_flags})
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
        info: Dict[str, str] = {
            "package": pkg,
            "path": path,
            "installer": installer,
            "version_name": "",
            "version_code": "",
            "high_value": pkg in HIGH_VALUE_PACKAGES,
            "uid": "",
            "system": system_app,
            "priv": priv_app,
        }

        # Fetch version details and additional metadata
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
                elif ln.startswith("userId=") or ln.startswith("uid="):
                    info["uid"] = ln.split("=", 1)[1].split()[0]
                elif ln.startswith("pkgFlags=") or ln.startswith("flags="):
                    flags = ln.split("[", 1)[-1].split("]", 1)[0].replace(",", " ")
                    if "SYSTEM" in flags:
                        info["system"] = True
                    if "PRIVILEGED" in flags:
                        info["priv"] = True
        except subprocess.CalledProcessError:
            pass

        packages.append(info)

    return packages


def export_permission_scan(
    results: List[Dict[str, Any]], json_path: str | Path | None = None, csv_path: str | Path | None = None
) -> None:
    """Export permission scan ``results`` to ``json_path`` and ``csv_path`` if given."""

    if json_path:
        out = Path(json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2))

    if csv_path:
        out_c = Path(csv_path)
        out_c.parent.mkdir(parents=True, exist_ok=True)
        with out_c.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["package", "permissions", "risk_flags"])
            for r in results:
                def _fmt_perm(p: Dict[str, Any]) -> str:
                    suffix = f"[{p['mode']}]" if p.get("mode") else ""
                    return f"{p['name']}{suffix}"
                perm_names = ",".join(_fmt_perm(p) for p in r.get("permissions", []))
                flags = ",".join(r.get("risk_flags", []))
                writer.writerow([r.get("package", ""), perm_names, flags])
