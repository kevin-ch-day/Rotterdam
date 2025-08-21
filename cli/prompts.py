"""Reusable CLI prompt helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from logs.logging_config import get_logger


logger = get_logger(__name__)

def prompt_existing_path(prompt: str, cancel_message: str) -> Optional[str]:
    """Prompt user for a filesystem path until an existing path is provided.

    If the user presses Enter without input, prints ``cancel_message`` and
    returns ``None``.
    """
    while True:
        path_str = input(prompt).strip()
        if not path_str:
            logger.info("prompt canceled")
            print(cancel_message)
            return None
        if Path(path_str).exists():
            logger.info("path provided", extra={"path": path_str})
            return path_str
        logger.warning("path does not exist", extra={"path": path_str})
        print("Status: Provided path does not exist.")

