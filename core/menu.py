#!/usr/bin/env python3
# menu.py
"""
Basic menu utilities for Android Tool.
- Renders a numbered menu with [0] Exit at the bottom (immutable rule).
- Robust input handling (whitespace, EOF, Ctrl+C).
- Optional shortcuts ('q'/'quit'/'exit' => 0).
- Optional default choice on empty input.
- Helper to run a loop that dispatches choices to a handler.

No external dependencies.
"""

from __future__ import annotations
import shutil
from typing import Callable, List, Optional


# -------- layout helpers (local copy; avoids cross-module deps) --------

def _term_width(default: int = 80) -> int:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default

def _divider(char: str = "=", width: Optional[int] = None) -> str:
    w = width or _term_width()
    return (char * max(1, w)).rstrip()


# -------- core renderer --------

def show_menu(
    title: str,
    options: List[str],
    *,
    exit_label: str = "Exit",
    prompt: str = "Select an option",
    allow_quit_shortcuts: bool = True,
    default_choice: Optional[int] = None,
) -> int:
    """
    Display a simple numbered menu and return the selected option number.

    Args:
        title: Menu title.
        options: List of option labels (1..N). Exit is implicitly 0 and always last.
        exit_label: Text shown for [0].
        prompt: Input prompt text.
        allow_quit_shortcuts: If True, 'q', 'quit', 'exit' => 0.
        default_choice: If set, hitting Enter with empty input returns this choice.
                        Must be 0..len(options). If invalid, it's ignored.

    Returns:
        int: 0..len(options). 0 is Exit.

    Behavior:
        - Whitespace is ignored.
        - Non-numeric input re-prompts (unless a quit shortcut is enabled & used).
        - Ctrl+C or EOF (Ctrl+D) returns 0 (Exit) safely.
    """
    valid_max = len(options)
    if default_choice is not None and not (0 <= default_choice <= valid_max):
        default_choice = None  # sanitize

    while True:
        # Header
        print()
        print(_divider("="))
        print(title.strip())
        print(_divider("-"))

        # Options (1..N)
        for i, label in enumerate(options, start=1):
            print(f"[{i}] {label}")

        # Exit (0)
        print(f"[0] {exit_label}")

        # Prompt (show default if set)
        suffix = f" [default: {default_choice}]" if default_choice is not None else ""
        try:
            raw = input(f"{prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive or user interruption => Exit
            return 0

        if not raw:
            if default_choice is not None:
                return default_choice
            # No default; fall through to re-prompt

        # Quit shortcuts
        if allow_quit_shortcuts:
            lowered = raw.lower()
            if lowered in ("q", "quit", "exit"):
                return 0

        # Numeric path
        if raw.isdigit():
            choice = int(raw)
            if 0 <= choice <= valid_max:
                return choice

        print("Invalid choice. Please try again.")


# -------- convenience loop --------

def run_menu_loop(
    title: str,
    options: List[str],
    handler: Callable[[int, str], None],
    *,
    exit_label: str = "Exit",
    allow_quit_shortcuts: bool = True,
    default_choice: Optional[int] = None,
) -> None:
    """
    Keep showing the menu until the user selects [0] Exit.
    For each non-zero selection, calls: handler(choice_number, option_label).

    Example:
        def on_pick(n, label):
            print(f"Picked {n}: {label}")

        run_menu_loop("Main Menu", ["Devices", "Packages"], on_pick)
    """
    while True:
        choice = show_menu(
            title,
            options,
            exit_label=exit_label,
            allow_quit_shortcuts=allow_quit_shortcuts,
            default_choice=default_choice,
        )
        if choice == 0:
            # graceful exit
            return
        label = options[choice - 1]  # safe: choice in 1..len(options)
        handler(choice, label)
