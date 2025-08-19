"""High-level sandbox analysis orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any, Iterable

from .runner import run_sandbox
from .permission_monitor import collect_permissions
from .network import sniff_network
from .frida_loader import resolve_hooks


def run_analysis(
    apk_path: str,
    outdir: Path,
    *,
    enable_hooks: Iterable[str] | None = None,
    disable_hooks: Iterable[str] | None = None,
) -> Dict[str, Any]:
    """Run sandbox, permission monitor and network capture for an APK.

    Parameters
    ----------
    apk_path: str
        Path to the APK file to analyze.
    outdir: Path
        Directory where analysis artifacts should be written.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing paths and collected findings:
        ``{"log": Path, "permissions": List[str], "network": List[Dict[str, str]],
        "metrics": Dict[str, Any], "messages": List[str]}``
    """
    outdir.mkdir(parents=True, exist_ok=True)

    hooks = resolve_hooks(enable_hooks, disable_hooks)
    log, metrics, messages = run_sandbox(apk_path, outdir, hooks=hooks)
    permissions: List[str] = collect_permissions(apk_path)
    network: List[Dict[str, str]] = sniff_network(apk_path)

    (outdir / "permissions.json").write_text(json.dumps(permissions, indent=2))
    (outdir / "network.json").write_text(json.dumps(network, indent=2))
    if metrics:
        (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    if messages:
        (outdir / "messages.json").write_text(json.dumps(messages, indent=2))

    return {
        "log": log,
        "permissions": permissions,
        "network": network,
        "metrics": metrics,
        "messages": messages,
    }
