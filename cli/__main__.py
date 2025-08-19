"""CLI entry point for the Android Tool."""
from __future__ import annotations

import argparse
import json

from . import run_main_menu


def main() -> None:
    """Execute the main menu."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output menus as JSON")
    args = parser.parse_args()

    result = run_main_menu(json_mode=args.json)
    if args.json and result is not None:
        print(json.dumps(result))
