"""Status line utilities for terminal output."""

from __future__ import annotations

import sys
from typing import TextIO

OK = "[OK]"
INF = "[*]"
NOTE = "[.]"
WARN = "[!]"
ERR = "[X]"

COLOR_PREFIX = {
    OK: "\033[32m",
    INF: "\033[36m",
    NOTE: "\033[36m",
    WARN: "\033[33m",
    ERR: "\033[31m",
}
RESET = "\033[0m"


def _emit(prefix: str, msg: str, *, ts: bool = False, stream: TextIO = sys.stdout) -> None:
    """Internal helper to print a prefixed message."""
    from . import config

    color = COLOR_PREFIX.get(prefix, "") if config.USE_COLOR else ""
    pre = f"{color}{prefix}{RESET}" if color else prefix
    stamp = f"{config.ts()} | " if ts else ""
    print(f"{pre} {stamp}{msg}", file=stream)


def info(msg: str, *, ts: bool = False) -> None:
    """Print an informational status line."""
    _emit(INF, msg, ts=ts, stream=sys.stdout)


def note(msg: str, *, ts: bool = False) -> None:
    """Print a secondary informational status line."""
    _emit(NOTE, msg, ts=ts, stream=sys.stdout)


def good(msg: str, *, ts: bool = False) -> None:
    """Print a success status line."""
    _emit(OK, msg, ts=ts, stream=sys.stdout)


def warn(msg: str, *, ts: bool = False) -> None:
    """Print a warning status line."""
    _emit(WARN, msg, ts=ts, stream=sys.stderr)


def fail(msg: str, *, ts: bool = False) -> None:
    """Print an error status line."""
    _emit(ERR, msg, ts=ts, stream=sys.stderr)


def warning(msg: str, *, ts: bool = False) -> None:
    """Alias for :func:`warn` for clearer call sites."""
    warn(msg, ts=ts)


def error(msg: str, *, ts: bool = False) -> None:
    """Alias for :func:`fail` for clearer call sites."""
    fail(msg, ts=ts)
