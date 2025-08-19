"""CLI entry point for the Android Tool."""
from __future__ import annotations

import uuid

from . import run_main_menu
from logging_config import StructuredLogger

# Generate a session identifier for this CLI invocation
SESSION_ID = str(uuid.uuid4())
StructuredLogger.set_session_id(SESSION_ID)


def main() -> None:
    """Execute the interactive main menu."""
    run_main_menu()
