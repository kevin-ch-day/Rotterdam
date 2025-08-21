#!/usr/bin/env python3
# File: platform/android/devices/processes.py
"""List running processes on a device via ADB (robust across Android ps variants)."""

from __future__ import annotations

import subprocess
from typing import List, Dict, Optional

from .adb import _adb_path, _run_adb
from core.errors import log_exception


def _try_ps(adb: str, serial: str, args: List[str], timeout: int = 10) -> Optional[str]:
    """
    Try running `adb -s <serial> shell ps ...`. Return stdout on success, None on failure.
    """
    try:
        proc = _run_adb([adb, "-s", serial, "shell", *args], timeout=timeout)
        return (proc.stdout or "").strip()
    except subprocess.CalledProcessError:
        return None


def _parse_ps_with_header(output: str) -> List[Dict[str, str]]:
    """
    Parse ps output that includes a header row. Detect USER/PID/NAME (or COMM/CMD/CMDLINE).
    Falls back to a reasonable default if columns are missing.
    """
    lines = [ln.rstrip() for ln in (output or "").splitlines() if ln.strip()]
    if not lines:
        return []

    header_idx = -1
    for i, ln in enumerate(lines[:3]):  # header is almost always in first line; be permissive
        up = ln.upper()
        if "PID" in up and ("USER" in up or "UID" in up):
            header_idx = i
            break

    # If we didn't find a header, bail to naive parse later.
    if header_idx == -1:
        return []

    header_cols = lines[header_idx].split()
    # Map potential name column variants
    name_candidates = ["NAME", "COMM", "COMMAND", "CMDLINE", "CMD"]
    col_map = {col.upper(): idx for idx, col in enumerate(header_cols)}

    # Identify columns (USER/UID, PID, NAME/COMM/COMMAND/…)
    user_col = col_map.get("USER", col_map.get("UID"))
    pid_col = col_map.get("PID")
    name_col = next((col_map[c] for c in name_candidates if c in col_map), None)

    results: List[Dict[str, str]] = []
    for ln in lines[header_idx + 1 :]:
        parts = ln.split()
        if pid_col is None or len(parts) <= (pid_col):
            continue
        try:
            user = parts[user_col] if user_col is not None and len(parts) > user_col else ""
            pid = parts[pid_col]
            if name_col is not None and len(parts) > name_col:
                name = parts[name_col]
            else:
                # If COMMAND is the last field and may contain spaces, use the last token as a safe fallback.
                name = parts[-1]
            results.append({"user": user, "pid": pid, "name": name})
        except Exception as exc:  # be resilient to odd rows
            log_exception("Failed to parse ps row with header", exc)
            continue

    return results


def _parse_ps_naive(output: str) -> List[Dict[str, str]]:
    """
    Naive parser for `ps` without reliable headers.
    Assumes: USER PID ... NAME  (uses last token as name).
    """
    processes: List[Dict[str, str]] = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        # Skip probable header lines
        if parts[0].upper() in {"USER", "UID"} or "PID" in (x.upper() for x in parts[:2]):
            continue
        if len(parts) < 2:
            continue
        user = parts[0]
        pid = parts[1]
        name = parts[-1]
        processes.append({"user": user, "pid": pid, "name": name})
    return processes


def parse_ps(output: str) -> List[Dict[str, str]]:
    """
    Parse ps output, preferring header-based parsing when available.
    """
    with_header = _parse_ps_with_header(output)
    if with_header:
        return with_header
    return _parse_ps_naive(output)


def list_processes(serial: str, timeout: int = 10) -> List[Dict[str, str]]:
    """
    Return running processes on the device identified by `serial`.
    Tries structured ps invocations first, falls back to plain ps.
    """
    adb = _adb_path()

    # Try modern/toybox-friendly forms first
    attempts = [
        ["ps", "-A", "-o", "USER,PID,NAME"],        # Android 8+/toybox
        ["ps", "-eo", "USER,PID,COMM"],             # alt formatting
        ["ps"],                                     # plain ps
    ]

    last_err: Optional[Exception] = None
    for args in attempts:
        try:
            out = _try_ps(adb, serial, args, timeout=timeout)
            if out is not None and out.strip():
                return parse_ps(out)
        except Exception as exc:  # catch unexpected tool/env errors and try next form
            last_err = exc
            continue

    if last_err:
        log_exception(f"Failed to list processes on device {serial}", last_err)

    # As a final attempt, raise a clear error instead of silently hiding issues.
    try:
        # Let this one raise if it fails so the caller sees a hard error.
        proc = _run_adb([adb, "-s", serial, "shell", "ps"], timeout=timeout)
        return parse_ps(proc.stdout or "")
    except subprocess.CalledProcessError as exc:
        log_exception(f"Failed to list processes on device {serial}", exc)
        raise RuntimeError("Failed to list processes") from exc
    except Exception as exc:
        log_exception(f"Unexpected error when listing processes on device {serial}", exc)
        return []
