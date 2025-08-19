#!/usr/bin/env python3
"""List running processes on a device via ADB."""

from __future__ import annotations

import subprocess
from typing import List, Dict

from .adb_utils import _adb_path, _run_adb
from app_utils.error_utils import log_exception


def parse_ps(output: str) -> List[Dict[str, str]]:
    """Parse `ps` output into dicts with user, pid, and name."""
    processes: List[Dict[str, str]] = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        # skip header line starting with USER or PID
        if parts[0].upper() in {"USER", "PID"}:
            continue
        if len(parts) < 2:
            continue
        user = parts[0]
        pid = parts[1]
        name = parts[-1]
        processes.append({"user": user, "pid": pid, "name": name})
    return processes


def list_processes(serial: str) -> List[Dict[str, str]]:
    """Return running processes on the device."""
    adb = _adb_path()
    try:
        proc = _run_adb([adb, "-s", serial, "shell", "ps"], timeout=10)
    except subprocess.CalledProcessError as exc:
        log_exception("Failed to list processes", exc)
        return []
    return parse_ps(proc.stdout or "")
