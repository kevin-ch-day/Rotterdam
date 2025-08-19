"""Command-line interface for running sandbox analysis with configurable hooks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .runtime import run_analysis


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run sandbox analysis")
    parser.add_argument("apk", help="Path to APK file to analyze")
    parser.add_argument("outdir", help="Directory to store analysis artifacts")
    parser.add_argument(
        "--enable-hook",
        action="append",
        dest="enable_hooks",
        default=None,
        help="Enable only the specified hook. Can be used multiple times.",
    )
    parser.add_argument(
        "--disable-hook",
        action="append",
        dest="disable_hooks",
        default=None,
        help="Disable the specified hook. Can be used multiple times.",
    )
    args = parser.parse_args(argv)

    run_analysis(
        args.apk,
        Path(args.outdir),
        enable_hooks=args.enable_hooks,
        disable_hooks=args.disable_hooks,
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
