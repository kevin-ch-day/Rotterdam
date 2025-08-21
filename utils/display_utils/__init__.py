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

# Canonical status helpers
from .status import info, ok, warn, fail, note, warning, error

# Backward-compatible alias
def good(*args, **kwargs):
    """Alias for ok()."""
    return ok(*args, **kwargs)


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
    "note",
    # aliases
    "good",
    "warning",
    "error",
]
