"""Simple sandbox runner stub with instrumentation hooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, List, Tuple, Any

from .instrumentation import FridaInstrumentation
from .metrics import compute_runtime_metrics


def run_sandbox(
    apk_path: str, outdir: Path, *, hooks: Iterable[str] | None = None
) -> Tuple[Path, Dict[str, Any], List[str]]:
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
    Tuple[Path, Dict[str, Any], List[str]]
        Path to the created log file, collected runtime metrics and raw
        messages emitted by instrumentation hooks.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    hooks = list(hooks or [])
    metrics_data: Dict[str, Any] = {}
    messages: List[str] = []

    # Load instrumentation and stream events into the metrics collector.
    with FridaInstrumentation(hooks) as instr:
        messages = list(instr.stream_events())
        if messages:
            perm_events = [e.split(":", 1)[1] for e in messages if e.startswith("PERMISSION:")]
            net_events = [e.split(":", 1)[1] for e in messages if e.startswith("NETWORK:")]
            file_events = [e.split(":", 1)[1] for e in messages if e.startswith("FILE_WRITE:")]
            metrics_data = compute_runtime_metrics(perm_events, net_events, file_events)

    log = outdir / "sandbox.log"
    log.write_text(f"Executed sandbox for {apk_path}\n")

    return log, metrics_data, messages
