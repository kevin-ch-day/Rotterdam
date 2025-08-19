#!/usr/bin/env python3
# config.py
"""Central configuration for Android Tool.

- Resolves project root robustly (even if imported from elsewhere).
- Defines standard output/log/screenshot directories.
- Provides timestamp helpers (12-hour AM/PM).
- Attempts to discover Android SDK root and ``adb`` binary.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, MutableMapping, Optional, Mapping

from config.loader import load as _load_config

# -----------------------------
# App metadata
# -----------------------------

APP_NAME: str = "Android Tool"
APP_VERSION: str = "0.0.1"

# Optional terminal colour output
USE_COLOR: bool = os.getenv("AT_COLOR", "0") not in ("0", "false", "False", "")

# Timestamp format (12-hour with AM/PM) e.g., 20250818-1234PM
TS_FMT_FILENAME: str = "%Y%m%d-%I%M%p"


# -----------------------------
# Project root discovery
# -----------------------------

def _discover_project_root() -> Path:
    """
    Try to find the project root by walking up from this file
    until we see a CLI entry point or an ``output`` directory.
    Fallback: parent of the ``core`` directory.
    """
    here = Path(__file__).resolve()
    # Common case: .../core/config.py
    start = here.parent  # core
    for p in [start] + list(start.parents):
        cli_entry = p / "cli" / "__main__.py"
        if cli_entry.exists() or (p / "output").is_dir():
            return p
    # Fallback to the parent of core
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
STORAGE_DIR: Path = PROJECT_ROOT / "storage"

def ensure_dirs() -> None:
    """Create required directories if missing."""
    for d in (OUTPUT_DIR, LOGS_DIR, SCREENSHOTS_DIR, STORAGE_DIR):
        d.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Global configuration
# -----------------------------


@dataclass
class GlobalConfig:
    """Container for runtime configuration loaded from file."""

    data: MutableMapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:  # pragma: no cover - trivial
        return key in self.data

    def load(
        self,
        path: Optional[Path] = None,
        *,
        schema: Mapping[str, type] | None = None,
        defaults: Mapping[str, Any] | None = None,
    ) -> None:
        """Load configuration from ``path`` using :mod:`config.loader`."""
        target = path or Path(os.getenv("AT_CONFIG", PROJECT_ROOT / "config.yaml"))
        if target.exists():
            self.data = _load_config(target, schema=schema, defaults=defaults)
        else:
            self.data = dict(defaults) if defaults else {}


CONFIG = GlobalConfig()



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


# Load configuration on import
CONFIG.load()
