"""Simple sandbox runner stub with instrumentation hooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .instrumentation import FridaInstrumentation
from .metrics import compute_runtime_metrics


def run_sandbox(apk_path: str, outdir: Path, *, hooks: Iterable[str] | None = None) -> Path:
    """Simulate running an APK inside a sandbox.

    Parameters
    ----------
    apk_path:
        Path to the APK that would be executed.
    outdir:
        Directory where logs and metrics should be written.
    hooks:
        Optional iterable of Frida script names to load before execution.

    Returns
    -------
    Path
        Path to the created log file.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    hooks = list(hooks or [])
    metrics_data = {}

    # Load instrumentation and stream events into the metrics collector.
    with FridaInstrumentation(hooks) as instr:
        events = list(instr.stream_events())
        if events:
            perm_events = [e.split(":", 1)[1] for e in events if e.startswith("PERMISSION:")]
            net_events = [e.split(":", 1)[1] for e in events if e.startswith("NETWORK:")]
            file_events = [e.split(":", 1)[1] for e in events if e.startswith("FILE_WRITE:")]
            metrics_data = compute_runtime_metrics(perm_events, net_events, file_events)

    log = outdir / "sandbox.log"
    log.write_text(f"Executed sandbox for {apk_path}\n")

    if metrics_data:
        (outdir / "metrics.json").write_text(json.dumps(metrics_data, indent=2))

    return log
