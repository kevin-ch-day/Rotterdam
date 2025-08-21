"""Status line utilities for terminal output."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import TextIO

# Try to source settings from app_config if available, else fall back.
try:
    from app_config.app_config import USE_COLOR as _CFG_USE_COLOR  # type: ignore
except Exception:
    _CFG_USE_COLOR = None  # type: ignore[assignment]

try:
    from app_config.app_config import ts as _cfg_ts  # type: ignore
except Exception:
    _cfg_ts = None  # type: ignore[assignment]


def _fallback_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Timestamp function (prefer app_config, else local)
_ts = _cfg_ts or _fallback_ts  # type: ignore[assignment]

# Determine color usage:
# - Respect app_config if provided
# - Otherwise enable only on TTY and when NO_COLOR is not set
if _CFG_USE_COLOR is not None:
    USE_COLOR: bool = bool(_CFG_USE_COLOR)
else:
    try:
        USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    except Exception:
        USE_COLOR = False

OK = "[OK]"
INF = "[*]"
NOTE = "[.]"
WARN = "[!]"
ERR = "[X]"

COLOR_PREFIX = {
    OK: "\033[32m",   # green
    INF: "\033[36m",  # cyan
    NOTE: "\033[36m", # cyan
    WARN: "\033[33m", # yellow
    ERR: "\033[31m",  # red
}
RESET = "\033[0m"


def _emit(prefix: str, msg: str, *, ts: bool = False, stream: TextIO = sys.stdout) -> None:
    """Internal helper to print a prefixed message."""
    use_color = USE_COLOR and hasattr(stream, "isatty") and stream.isatty()
    color = COLOR_PREFIX.get(prefix, "") if use_color else ""
    pre = f"{color}{prefix}{RESET}" if color else prefix
    stamp = f"{_ts()} | " if ts else ""
    print(f"{pre} {stamp}{msg}", file=stream)


def info(msg: str, *, ts: bool = False) -> None:
    """Print an informational status line."""
    _emit(INF, msg, ts=ts, stream=sys.stdout)


def ok(msg: str, *, ts: bool = False) -> None:
    """Print a success status line."""
    _emit(OK, msg, ts=ts, stream=sys.stdout)


def warn(msg: str, *, ts: bool = False) -> None:
    """Print a warning status line."""
    _emit(WARN, msg, ts=ts, stream=sys.stderr)


def fail(msg: str, *, ts: bool = False) -> None:
    """Print an error status line."""
    _emit(ERR, msg, ts=ts, stream=sys.stderr)


# Backward-compatible aliases (do not remove yet)
def note(msg: str, *, ts: bool = False) -> None:
    """Alias for info (secondary informational line)."""
    info(msg, ts=ts)


def good(msg: str, *, ts: bool = False) -> None:
    """Alias for ok (success line)."""
    ok(msg, ts=ts)


def warning(msg: str, *, ts: bool = False) -> None:
    """Alias for warn (clearer call sites)."""
    warn(msg, ts=ts)


def error(msg: str, *, ts: bool = False) -> None:
    """Alias for fail (clearer call sites)."""
    fail(msg, ts=ts)
