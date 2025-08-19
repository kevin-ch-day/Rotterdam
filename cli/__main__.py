"""CLI entry point for the Android Tool."""
from __future__ import annotations

import argparse
import json
import uuid

from . import run_main_menu

# Optional structured logging support
try:
    from logging_config import StructuredLogger  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - logging is optional
    class StructuredLogger:  # type: ignore[override]
        @staticmethod
        def set_session_id(_: str) -> None:
            pass

# Generate a session identifier for this CLI invocation
SESSION_ID = str(uuid.uuid4())
StructuredLogger.set_session_id(SESSION_ID)


def main() -> None:
    """Execute the main menu."""
    parser = argparse.ArgumentParser(description="Android Tool CLI")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output menus as JSON (machine-readable UI)",
    )
    args = parser.parse_args()

    result = run_main_menu(json_mode=args.json)
    if args.json and result is not None:
        print(json.dumps(result))


if __name__ == "__main__":  # pragma: no cover
    main()
