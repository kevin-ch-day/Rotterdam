#!/usr/bin/env python3
"""Utilities for collecting and normalizing installed package info."""

from __future__ import annotations

import logging
import subprocess
from typing import Any, Dict, List, Tuple

from ..devices.adb import _run_adb
from ..devices.packages import HIGH_VALUE_PACKAGES


logger = logging.getLogger(__name__)

UNKNOWN = "unknown"


def parse_pkg_list(text: str) -> Dict[str, str]:
    """Parse ``pm list packages -f`` output into a mapping of package→path.

    The parser is resilient to stray whitespace or malformed lines and
    normalizes package names to lowercase.
    """

    packages: Dict[str, str] = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or not line.startswith("package:"):
            continue
        line = line[len("package:") :]
        if "=" not in line:
            # Unexpected format; skip
            continue
        path, pkg = line.split("=", 1)
        pkg = pkg.strip().lower()
        path = path.strip()
        if not pkg or not path or "=" in pkg:
            continue
        packages[pkg] = path
    return packages


DEFAULT_TIMEOUT = 2.0


def _flags_from_path(path: str) -> Tuple[bool, bool]:
    """Infer system and priv-app flags from an APK path."""

    p = path.lower()
    is_priv = "/priv-app/" in p
    is_system = is_priv or any(
        seg in p for seg in ("/system/", "/system_ext/", "/product/", "/vendor/")
    )
    return is_system, is_priv


def normalize_inventory(
    adb: str, serial: str, *, fast: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """Return normalized package inventory for the given device.

    ``fast`` skips per-package ``dumpsys`` queries to reduce runtime. All
    subprocess calls are bounded by ``timeout`` seconds and failures return
    partial information rather than raising.
    """

    # list packages with one retry after `adb start-server`
    proc = None
    for attempt in range(2):
        try:
            proc = _run_adb(
                [adb, "-s", serial, "shell", "pm", "list", "packages", "-f"],
                timeout=timeout,
            )
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            if attempt == 0:
                try:
                    _run_adb([adb, "start-server"], timeout=timeout)
                except Exception:
                    pass
                continue
            logger.warning("failed to list packages on %s: %s", serial, exc)
            return []

    inventory: Dict[str, Dict[str, Any]] = {}
    for pkg, path in parse_pkg_list(proc.stdout or "").items():
        is_system, is_priv = _flags_from_path(path)
        inventory[pkg] = {
            "package": pkg,
            "apk_path": path or UNKNOWN,
            "installer": UNKNOWN,
            "uid": UNKNOWN,
            "version": UNKNOWN,
            "system": is_system,
            "priv_app": is_priv,
            "high_value": pkg in HIGH_VALUE_PACKAGES,
        }

    # installer info
    try:
        proc = _run_adb(
            [adb, "-s", serial, "shell", "pm", "list", "packages", "-i"],
            timeout=timeout,
        )
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            line = line[len("package:") :]
            if " installer=" not in line:
                continue
            pkg, installer = line.split(" installer=", 1)
            pkg = pkg.strip().lower()
            installer = installer.strip() or UNKNOWN
            if pkg in inventory:
                inventory[pkg]["installer"] = installer
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("installer query failed for %s: %s", serial, exc)

    # uid info
    try:
        proc = _run_adb(
            [adb, "-s", serial, "shell", "cmd", "package", "list", "packages", "-U"],
            timeout=timeout,
        )
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            rest = line[len("package:") :]
            parts = rest.split()
            pkg = parts[0].strip().lower()
            uid = UNKNOWN
            for p in parts[1:]:
                if p.startswith("uid:"):
                    uid = p.split(":", 1)[1]
                    break
            if pkg in inventory:
                inventory[pkg]["uid"] = uid
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("uid query failed for %s: %s", serial, exc)

    # version and flag info
    dumpsys_ok = not fast
    for pkg in list(inventory.keys()):
        if not dumpsys_ok:
            break
        try:
            dump = _run_adb(
                [adb, "-s", serial, "shell", "dumpsys", "package", pkg],
                timeout=timeout,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("dumpsys for %s failed: %s", pkg, exc)
            dumpsys_ok = False
            continue
        version = UNKNOWN
        is_system = False
        is_priv = False
        for ln in (dump.stdout or "").splitlines():
            ln = ln.strip()
            if ln.startswith("versionName="):
                version = ln.split("=", 1)[1].strip() or UNKNOWN
            elif ln.startswith("flags=") or ln.startswith("pkgFlags="):
                up = ln.upper()
                if "SYSTEM" in up:
                    is_system = True
                if "PRIV" in up:
                    is_priv = True
        inventory[pkg]["version"] = version
        inventory[pkg]["system"] = is_system
        inventory[pkg]["priv_app"] = is_priv

    return sorted(inventory.values(), key=lambda p: p["package"])
