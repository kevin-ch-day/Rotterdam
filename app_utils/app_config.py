#!/usr/bin/env python3
# app_config.py
"""
Central configuration for Android Tool.

- Resolves project root robustly (even if imported from elsewhere).
- Defines standard output/log/screenshot directories.
- Provides timestamp helpers (12-hour AM/PM).
- Attempts to discover Android SDK root and adb binary.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# -----------------------------
# App metadata
# -----------------------------

APP_NAME: str = "Android Tool"
APP_VERSION: str = "0.0.1"

# Timestamp format (12-hour with AM/PM) e.g., 20250818-1234PM
TS_FMT_FILENAME: str = "%Y%m%d-%I%M%p"


# -----------------------------
# Project root discovery
# -----------------------------

def _discover_project_root() -> Path:
    """
    Try to find the project root by walking up from this file
    until we see a 'main.py' or 'output' directory.
    Fallback: parent of the 'app_utils' directory.
    """
    here = Path(__file__).resolve()
    # Common case: .../app_utils/app_config.py
    start = here.parent  # app_utils
    for p in [start] + list(start.parents):
        if (p / "main.py").exists() or (p / "output").is_dir():
            return p
    # Fallback to the parent of app_utils
    try:
        return here.parents[1]
    except IndexError:
        return here.parent

PROJECT_ROOT: Path = _discover_project_root()


# -----------------------------
# Standard directories
# -----------------------------

OUTPUT_DIR: Path = PROJECT_ROOT / "output"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
SCREENSHOTS_DIR: Path = OUTPUT_DIR / "device_screenshots"

def ensure_dirs() -> None:
    """Create required directories if missing."""
    for d in (OUTPUT_DIR, LOGS_DIR, SCREENSHOTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Timestamp helpers
# -----------------------------

def ts(fmt: str = TS_FMT_FILENAME) -> str:
    """
    Return a local timestamp string (default suited for filenames).
    Example: '20250818-1234PM'
    """
    return datetime.now().strftime(fmt)

def dated_filename(prefix: str, suffix: str, directory: Optional[Path] = None) -> Path:
    """
    Build a timestamped filename inside 'directory' (default OUTPUT_DIR).
    Example: dated_filename('logcat_', '.txt', LOGS_DIR)
             -> logs/logcat_20250818-1234PM.txt
    """
    directory = directory or OUTPUT_DIR
    return directory / f"{prefix}{ts()}{suffix}"


# -----------------------------
# Android SDK / ADB discovery
# -----------------------------

def _sdk_root_from_env() -> Optional[Path]:
    """Return SDK root from env vars if set."""
    for env in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        val = os.getenv(env)
        if val:
            p = Path(val).expanduser()
            if p.exists():
                return p
    return None

def get_sdk_root(default: Path = Path("/opt/android-sdk")) -> Path:
    """
    Resolve the Android SDK root. Preference order:
    1) ANDROID_SDK_ROOT / ANDROID_HOME
    2) /opt/android-sdk (default)
    """
    return _sdk_root_from_env() or default

def get_adb_path() -> str:
    """
    Resolve 'adb' binary path:
    - If SDK root has platform-tools/adb, use that absolute path.
    - Else fall back to 'adb' (expect on PATH).
    """
    sdk = get_sdk_root()
    candidate = sdk / "platform-tools" / "adb"
    return str(candidate) if candidate.exists() else "adb"


# -----------------------------
# Simple config echo (optional)
# -----------------------------

def debug_summary() -> str:
    """Return a small, human-readable summary of key paths/settings."""
    return "\n".join([
        f"App           : {APP_NAME} v{APP_VERSION}",
        f"Project Root  : {PROJECT_ROOT}",
        f"Output Dir    : {OUTPUT_DIR}",
        f"Logs Dir      : {LOGS_DIR}",
        f"Screenshots   : {SCREENSHOTS_DIR}",
        f"SDK Root      : {get_sdk_root()}",
        f"ADB Path      : {get_adb_path()}",
    ])
