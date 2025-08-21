#!/usr/bin/env python3
# display.py
"""
General display utilities for Android Tool.
- ASCII-only (no external deps)
- Terminal-aware widths
- Clean banners/headers/dividers
- Robust status lines (info/warn/error/ok), optional timestamps, stderr routing
- Handy helpers: clear(), bullets, key/value, truncation, byte formatting
- Re-exports ``print_table`` from :mod:`core.table`
"""

from __future__ import annotations

import os
import shutil
from textwrap import wrap
from typing import Iterable, Sequence, Any, Optional

from ...core import config
from ...core import table as tables
from .status import info, good, warn, fail

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


# Status line helpers re-exported from :mod:`core.status`


# -----------------------------
# Convenience wrappers
# -----------------------------

def print_app_banner(subtitle: Optional[str] = None, *, boxed: bool = False) -> None:
    """Standard app banner using project metadata."""
    title = f"{config.APP_NAME} v{config.APP_VERSION}"
    print(banner(title, subtitle=subtitle, boxed=boxed))

def print_section(title: str, underline: str = "=") -> None:
    """Section header with a blank line around it."""
    print()
    print(header(title, underline=underline))
    print()


def render_menu(
    title: str,
    options: Sequence[str],
    exit_label: str = "Back",
    *,
    serial: Optional[str] = None,
) -> str:
    """Return a framed menu string.

    The menu is rendered inside a simple box using box-drawing characters.
    ``serial`` can be supplied to show contextual information (e.g. the
    connected device serial).
    """

    header = title.strip()
    if serial:
        header = f"{header} (serial: {serial})"

    # Determine width based on longest line
    body = [f"[{i}] {opt}" for i, opt in enumerate(options, start=1)]
    body.append(f"[0] {exit_label}")
    width = max(len(header), *(len(line) for line in body)) + 4

    top = "╭" + "─" * (width - 2) + "╮"
    sep = "├" + "─" * (width - 2) + "┤"
    bottom = "╰" + "─" * (width - 2) + "╯"

    lines = [top, f"│ {header.ljust(width - 4)} │", sep]
    for line in body:
        lines.append(f"│ {line.ljust(width - 4)} │")
    lines.append(bottom)
    return "\n".join(lines)


def print_menu(title: str, options: Sequence[str], exit_label: str = "Exit") -> None:
    """Convenience wrapper around :func:`render_menu` that prints the menu."""
    print(render_menu(title, options, exit_label))


def prompt_choice(
    valid_options: Iterable[str],
    default: Optional[str] = None,
    message: str = "Select an option",
) -> str:
    """Prompt the user until a valid option is entered.

    Parameters
    ----------
    valid_options:
        Iterable of accepted string choices.
    default:
        Value returned when the user presses Enter without input.

    Returns
    -------
    str
        The chosen option. ``"q"`` is returned if the user requests to quit
        via ``q``/``Q`` or triggers EOF/KeyboardInterrupt.
    """

    options = {str(opt) for opt in valid_options}

    while True:
        try:
            raw = input(f"{message}: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "q"

        if not raw:
            if default is not None:
                return default
            warn("Invalid choice. Please try again.")
            continue

        if raw.lower() == "q":
            return "q"

        if raw in options:
            return raw

        warn("Invalid choice. Please try again.")


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

# -----------------------------
# Re-export table utilities
# -----------------------------

print_table = tables.print_table
