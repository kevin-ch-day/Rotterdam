"""High-level sandbox analysis orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

from .sandbox_runner import run_sandbox
from .permission_monitor import collect_permissions
from .network_sniffer import sniff_network


def analyze_apk(apk_path: str, outdir: Path) -> Dict[str, Any]:
    """Run sandbox, permission monitor and network sniffer for an APK.

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
        ``{"log": Path, "permissions": List[str], "network": List[Dict[str, str]]}``
    """
    outdir.mkdir(parents=True, exist_ok=True)

    log = run_sandbox(apk_path, outdir)
    permissions: List[str] = collect_permissions(apk_path)
    network: List[Dict[str, str]] = sniff_network(apk_path)

    (outdir / "permissions.json").write_text(json.dumps(permissions, indent=2))
    (outdir / "network.json").write_text(json.dumps(network, indent=2))

    return {"log": log, "permissions": permissions, "network": network}
