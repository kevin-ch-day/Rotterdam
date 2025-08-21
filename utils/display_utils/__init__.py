"""Helpers for formatted terminal output."""

from .display import (
    banner,
    clear_screen,
    divider,
    header,
    print_app_banner,
    print_bullets,
    print_kv,
    print_menu,
    print_section,
    print_table,
    prompt_choice,
    render_menu,
    term_width,
    wrap_text,
)

# Standard status helpers
from .status import fail, ok, info, warn  # canonical names

# Backward-compatible aliases (some callers use these)
def good(*args, **kwargs):
    return ok(*args, **kwargs)


def warning(*args, **kwargs):
    return warn(*args, **kwargs)


def error(*args, **kwargs):
    return fail(*args, **kwargs)


def note(*args, **kwargs):
    # Neutral/low-importance message; map to info
    return info(*args, **kwargs)


__all__ = [
    "banner",
    "clear_screen",
    "divider",
    "header",
    "print_app_banner",
    "print_bullets",
    "print_kv",
    "print_menu",
    "print_section",
    "prompt_choice",
    "render_menu",
    "term_width",
    "wrap_text",
    "print_table",
    # status helpers (canonical)
    "info",
    "ok",
    "warn",
    "fail",
    # aliases for backward compatibility
    "good",
    "warning",
    "error",
    "note",
]
