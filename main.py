"""Top-level entry point for the Rotterdam CLI."""

from __future__ import annotations

import argparse
import json

from app_config import app_config
from utils.logging_utils.app_logger import app_logger
from utils.logging_utils.logging_config import configure_logging


def main() -> None:
    """Run the CLI menu."""
    parser = argparse.ArgumentParser(prog=app_config.APP_NAME)
    parser.add_argument("--json", action="store_true", help="Output menus as JSON")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--log-to-stdout",
        action="store_true",
        help="Also emit logs to stdout",
    )
    args = parser.parse_args()

    if args.version:
        print(f"{app_config.APP_NAME} v{app_config.APP_VERSION}")
        return

    configure_logging("cli", log_to_stdout=args.log_to_stdout)

    # Import CLI menus after configuring logging so any module-level loggers
    # respect the desired handlers.
    from cli import run_main_menu

    logger = app_logger.get_logger(__name__)
    logger.info("Launching CLI", extra={"json": args.json})

    result = run_main_menu(json_mode=args.json)
    if args.json and result is not None:
        print(json.dumps(result))


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
