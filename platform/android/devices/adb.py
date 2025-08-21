#!/usr/bin/env python3
"""Shared helpers for invoking ``adb`` commands."""

from __future__ import annotations

import shutil
import subprocess
from app_config import app_config


def _run_adb(args: list[str], *, timeout: int = 8) -> subprocess.CompletedProcess:
    """Run adb with robust defaults and return the completed process."""
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout)


def _adb_path() -> str:
    """Return the best ``adb`` path available on this system."""
    path = app_config.get_adb_path()
    which = shutil.which("adb")
    try:
        subprocess.run(
            [path, "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return path
    except Exception:
        return which or path
