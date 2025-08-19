"""Reusable CLI prompt helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def prompt_existing_path(prompt: str, cancel_message: str) -> Optional[str]:
    """Prompt user for a filesystem path until an existing path is provided.

    If the user presses Enter without input, prints ``cancel_message`` and
    returns ``None``.
    """
    while True:
        path_str = input(prompt).strip()
        if not path_str:
            print(cancel_message)
            return None
        if Path(path_str).exists():
            return path_str
        print("Status: Provided path does not exist.")

