"""Top-level entry point for the Android Tool CLI."""
from __future__ import annotations

from cli import run_main_menu
from logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Run the interactive CLI menu."""
    logger.info("Launching CLI")
    run_main_menu()


if __name__ == "__main__":
    main()
