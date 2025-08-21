#!/usr/bin/env python3
# File: app_config/app_config.py
# config.py
"""Central configuration for Rotterdam.

- Resolves project root robustly (even if imported from elsewhere).
- Defines standard output/log/screenshot directories.
- Provides timestamp helpers (12-hour AM/PM).
- Attempts to discover Android SDK root and ``adb`` binary.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

from app_config.load_configs import load as _load_config

# -----------------------------
# App metadata
# -----------------------------

APP_NAME: str = "Rotterdam"
APP_VERSION: str = "0.0.1"
APP_VENDOR: str = "Rotterdam Project"
APP_HOMEPAGE: str = "https://rotterdam.example.com"


# Optional terminal colour output
def _env(key_new: str, key_old: str | None = None, default: str | None = None) -> str | None:
    """Fetch environment variable ``key_new`` with fallback to ``key_old``.

    Emits a :class:`DeprecationWarning` if the legacy key is used.
    """
    val = os.getenv(key_new)
    if val is not None:
        return val
    if key_old and (legacy := os.getenv(key_old)) is not None:
        warnings.warn(
            f"{key_old} is deprecated; use {key_new}",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy
    return default


USE_COLOR: bool = _env("ROTTERDAM_COLOR", "AT_COLOR", "0") not in (
    "0",
    "false",
    "False",
    "",
)

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

# Base data directory (dev: ~/.rotterdam, prod: overridable via env)
DATA_DIR: Path = Path(
    _env("ROTTERDAM_DATA_DIR", default=str(Path.home() / ".rotterdam"))
).expanduser()

EVIDENCE_DIR: Path = DATA_DIR / "evidence"
TMP_DIR: Path = DATA_DIR / "tmp"
LOGS_DIR: Path = DATA_DIR / "logs"
REPORTS_DIR: Path = DATA_DIR / "reports"

OUTPUT_DIR: Path = REPORTS_DIR  # Backwards compatibility alias
STORAGE_DIR: Path = TMP_DIR
SCREENSHOTS_DIR: Path = EVIDENCE_DIR / "device_screenshots"


def ensure_dirs() -> None:
    """Create required directories if missing."""
    for d in (EVIDENCE_DIR, TMP_DIR, LOGS_DIR, REPORTS_DIR, SCREENSHOTS_DIR):
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
        env_path = _env("ROTTERDAM_CONFIG", "AT_CONFIG")
        default_path = PROJECT_ROOT / "config.yaml"
        target = path or Path(env_path or default_path)
        if target.exists():
            self.data = _load_config(target, schema=schema, defaults=defaults)
        else:
            self.data = dict(defaults) if defaults else {}


CONFIG = GlobalConfig()


# -----------------------------
# Database configuration
# -----------------------------


def get_database_url() -> str:
    """Return a SQLAlchemy database URL constructed from the environment.

    The resolution order is:

    1. ``DATABASE_URL`` if set.
    2. Individual MySQL settings (``DB_USER``, ``DB_PASSWORD``, ``DB_HOST``,
       ``DB_PORT``, ``DB_NAME``).
    3. Fallback to an in-memory SQLite database.
    """

    url = os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("DB_USER")
    name = os.getenv("DB_NAME")
    if user and name:
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        auth = f":{password}" if password else ""
        return f"mysql+mysqlconnector://{user}{auth}@{host}:{port}/{name}"

    return "sqlite:///:memory:"


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
    return "\n".join(
        [
            f"App           : {APP_NAME} v{APP_VERSION}",
            f"Data Dir      : {DATA_DIR}",
            f"Reports Dir   : {REPORTS_DIR}",
            f"Logs Dir      : {LOGS_DIR}",
            f"Screenshots   : {SCREENSHOTS_DIR}",
            f"SDK Root      : {get_sdk_root()}",
            f"ADB Path      : {get_adb_path()}",
        ]
    )


# Load configuration on import
CONFIG.load()
