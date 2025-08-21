"""Entry point for running sandbox analysis as a script."""

from android.analysis.dynamic.__main__ import main

__all__ = ["main"]

if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()

