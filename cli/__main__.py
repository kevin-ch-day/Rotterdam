"""CLI entry point for the Android Tool."""
from __future__ import annotations

from . import run_main_menu


def main() -> None:
    run_main_menu()


if __name__ == "__main__":  # pragma: no cover - simple CLI
    main()
