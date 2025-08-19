"""Status line utilities for terminal output."""

from __future__ import annotations

import sys
from typing import TextIO

OK = "[OK]"
INF = "[*]"
WARN = "[!]"
ERR = "[X]"


def _emit(prefix: str, msg: str, *, ts: bool = False, stream: TextIO = sys.stdout) -> None:
    """Internal helper to print a prefixed message."""
    from . import app_config

    stamp = f"{app_config.ts()} | " if ts else ""
    print(f"{prefix} {stamp}{msg}", file=stream)


def info(msg: str, *, ts: bool = False) -> None:
    """Print an informational status line."""
    _emit(INF, msg, ts=ts, stream=sys.stdout)


def good(msg: str, *, ts: bool = False) -> None:
    """Print a success status line."""
    _emit(OK, msg, ts=ts, stream=sys.stdout)


def warn(msg: str, *, ts: bool = False) -> None:
    """Print a warning status line."""
    _emit(WARN, msg, ts=ts, stream=sys.stderr)


def fail(msg: str, *, ts: bool = False) -> None:
    """Print an error status line."""
    _emit(ERR, msg, ts=ts, stream=sys.stderr)
