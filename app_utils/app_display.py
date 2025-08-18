#!/usr/bin/env python3
# app_display.py
"""
General display utilities for Android Tool.
- ASCII-only (no external deps)
- Terminal-aware widths
- Clean banners/headers/dividers
- Robust status lines (info/warn/error/ok), optional timestamps, stderr routing
- Handy helpers: clear(), bullets, key/value, truncation, byte formatting
- Re-exports print_table from app_table_display
"""

from __future__ import annotations

import os
import sys
import shutil
from textwrap import wrap
from typing import Iterable, Sequence, Any, Optional

from . import app_config
from . import app_table_display as tables


# -----------------------------
# Terminal / layout
# -----------------------------

def term_width(default: int = 80) -> int:
    """Best-effort terminal width (falls back safely)."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default


def divider(char: str = "-", width: Optional[int] = None, margin: int = 0) -> str:
    """
    Horizontal rule. `margin` adds leading/trailing spaces (clamped).
    """
    w = max(1, (width or term_width()) - margin * 2)
    line = (char or "-") * w
    return f'{" " * margin}{line}'


def header(text: str, underline: str = "-") -> str:
    """Section header with underline sized to the text length."""
    line = text.strip()
    return f"{line}\n{(underline or '-')[0] * max(1, len(line))}"


def banner(title: str, subtitle: Optional[str] = None, boxed: bool = False) -> str:
    """
    Top banner. If boxed=True, uses a box; else wide dividers.
    """
    title = title.strip()
    w = term_width()
    if boxed:
        inner_w = min(max(len(title), len(subtitle or "")) + 6, w - 2)
        top = "+" + "-" * (inner_w - 2) + "+"
        mid = f"| {title.center(inner_w - 4)} |"
        lines = [top, mid]
        if subtitle:
            lines.append(f"| {subtitle.strip().center(inner_w - 4)} |")
        lines.append(top)
        return "\n".join(lines)
    else:
        top = divider("=", w)
        mid = title.center(w)
        parts = [top, mid]
        if subtitle:
            parts.append(subtitle.strip().center(w))
        parts.append(top)
        return "\n".join(parts)


def clear_screen() -> None:
    """Clear terminal (best effort)."""
    os.system("cls" if os.name == "nt" else "clear")


# -----------------------------
# Status lines
# -----------------------------

OK   = "[OK]"
INF  = "[*]"
WARN = "[!]"
ERR  = "[X]"

def _emit(prefix: str, msg: str, *, ts: bool = False, stream = sys.stdout) -> None:
    stamp = f"{app_config.ts()} | " if ts else ""
    print(f"{prefix} {stamp}{msg}", file=stream)

def info(msg: str, *, ts: bool = False) -> None:
    _emit(INF, msg, ts=ts, stream=sys.stdout)

def good(msg: str, *, ts: bool = False) -> None:
    _emit(OK, msg, ts=ts, stream=sys.stdout)

def warn(msg: str, *, ts: bool = False) -> None:
    _emit(WARN, msg, ts=ts, stream=sys.stderr)

def fail(msg: str, *, ts: bool = False) -> None:
    _emit(ERR, msg, ts=ts, stream=sys.stderr)


# -----------------------------
# Convenience wrappers
# -----------------------------

def print_app_banner(subtitle: Optional[str] = None, *, boxed: bool = False) -> None:
    """Standard app banner using config metadata."""
    title = f"{app_config.APP_NAME} v{app_config.APP_VERSION}"
    print(banner(title, subtitle=subtitle, boxed=boxed))

def print_section(title: str, underline: str = "=") -> None:
    """Section header with a blank line around it."""
    print()
    print(header(title, underline=underline))
    print()


# -----------------------------
# Simple text helpers
# -----------------------------

def print_bullets(items: Iterable[str], bullet: str = " - ") -> None:
    """Print a simple bullet list."""
    for it in items:
        print(f"{bullet}{it}")

def print_kv(pairs: Sequence[tuple[str, Any]], key_pad: int = 18) -> None:
    """
    Print aligned key/value lines.
    pairs: iterable of (key, value)
    """
    for k, v in pairs:
        key = str(k).rstrip(":")
        val = "" if v is None else str(v)
        print(f"{key:<{key_pad}} : {val}")

def wrap_text(text: str, width: Optional[int] = None) -> str:
    """Wrap a long string to terminal width."""
    w = width or (term_width() - 2)
    return "\n".join(wrap(text, w))

def truncate_middle(s: str, max_len: int) -> str:
    """
    Truncate long strings in the middle with an ellipsis.
    e.g., '/very/long/path/file.txt' -> '/very/lo…file.txt'
    """
    if len(s) <= max_len or max_len < 5:
        return s if len(s) <= max_len else s[:max_len]
    half = (max_len - 1) // 2
    return s[:half] + "…" + s[-(max_len - half - 1):]

# -----------------------------
# Re-export table utilities
# -----------------------------

print_table = tables.print_table
