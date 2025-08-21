"""CLI entry point for the Android Tool."""

from __future__ import annotations

import argparse
import json
import uuid

from . import run_main_menu

# Optional structured logging support
try:
    from utils.logging_utils.app_logger import app_logger  # type: ignore[attr-defined]
    from utils.logging_utils.log_helpers import LoggingHelper

    logger = app_logger.get_logger(__name__)
    LoggingHelper.info("CLI initialized", logger_name=__name__)
except Exception:  # pragma: no cover - logging is optional

    class _AppLogger:  # type: ignore[override]
        def set_session_id(self, _: str) -> None:
            pass

        def get_logger(self, *_: str, **__: str):  # noqa: ANN001 - signature mirrors real method
            return None

    app_logger = _AppLogger()  # type: ignore
    logger = None

# Generate a session identifier for this CLI invocation
SESSION_ID = str(uuid.uuid4())
app_logger.set_session_id(SESSION_ID)


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
