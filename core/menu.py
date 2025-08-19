#!/usr/bin/env python3
# menu.py
"""
Basic menu utilities for Android Tool.
- Renders a numbered menu with [0] Exit at the bottom (immutable rule).
- Robust input handling (whitespace, EOF, Ctrl+C).
- Optional shortcuts ('q'/'quit'/'exit' => 0).
- Optional default choice on empty input.
- Helper to run a loop that dispatches choices to a handler.

Uses :mod:`core.display` for consistent rendering.
"""

from __future__ import annotations
from typing import Callable, List, Optional

from . import display


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

    valid = {str(i) for i in range(valid_max + 1)}
    default_str = str(default_choice) if default_choice is not None else None

    while True:
        print()
        print(display.render_menu(title, options, exit_label=exit_label))

        choice = display.prompt_choice(valid, default_str, message=prompt)
        if choice == "q":
            if allow_quit_shortcuts:
                return 0
            display.warn("Invalid choice. Please try again.")
            continue
        return int(choice)


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
