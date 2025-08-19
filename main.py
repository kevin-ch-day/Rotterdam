"""Top-level entry point for the Android Tool CLI."""
from __future__ import annotations

import argparse
import json

from cli import run_main_menu
from logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Run the CLI menu."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output menus as JSON")
    args = parser.parse_args()

    logger.info("Launching CLI", extra={"json": args.json})
    result = run_main_menu(json_mode=args.json)
    if args.json and result is not None:
        print(json.dumps(result))


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
