"""Simple sandbox runner stub with instrumentation hooks."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Dict, List, Tuple, Any
import shutil

from .instrumentation import FridaInstrumentation
from .metrics import compute_runtime_metrics


def run_sandbox(
    apk_path: str, outdir: Path, *, hooks: Iterable[str] | None = None
) -> Tuple[Path, Dict[str, Any], List[str]]:
    """Simulate running an APK inside a sandbox.

    Parameters
    ----------
    apk_path:
        Path to the APK that would be executed. A :class:`FileNotFoundError`
        is raised if the file does not exist to prevent silent analysis of
        missing inputs.
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
    apk = Path(apk_path)
    if not apk.is_file():
        raise FileNotFoundError(f"APK not found: {apk_path}")

    outdir.mkdir(parents=True, exist_ok=True)
    hooks = list(hooks or [])
    metrics_data: Dict[str, Any] = {}
    messages: List[str] = []

    with TemporaryDirectory(prefix="rotterdam_sandbox_") as tmpdir:
        temp_path = Path(tmpdir)
        # Load instrumentation and stream events into the metrics collector inside
        # an isolated temporary workspace. This provides a basic snapshot that is
        # automatically discarded at the end of the run, making the sandbox more
        # resistant to persistence and evasion attempts.
        with FridaInstrumentation(hooks) as instr:
            messages = list(instr.stream_events())
            if messages:
                perm_events = [e.split(":", 1)[1] for e in messages if e.startswith("PERMISSION:")]
                net_events = [e.split(":", 1)[1] for e in messages if e.startswith("NETWORK:")]
                file_events = [e.split(":", 1)[1] for e in messages if e.startswith("FILE_WRITE:")]
                metrics_data = compute_runtime_metrics(perm_events, net_events, file_events)

        log_path = temp_path / "sandbox.log"
        log_path.write_text(f"Executed sandbox for {apk}\n")
        final_log = outdir / "sandbox.log"
        shutil.copy2(log_path, final_log)

    return final_log, metrics_data, messages
