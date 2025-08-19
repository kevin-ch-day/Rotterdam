"""Simple sandbox runner stub."""

from __future__ import annotations

from pathlib import Path


def run_sandbox(apk_path: str, outdir: Path) -> Path:
    """Simulate running an APK inside a sandbox.

    The function simply writes a log file indicating that the APK was
    executed.  It returns the path to the created log file.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    log = outdir / "sandbox.log"
    log.write_text(f"Executed sandbox for {apk_path}\n")
    return log
