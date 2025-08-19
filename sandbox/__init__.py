"""Sandbox runtime analysis utilities."""

from __future__ import annotations

# Core utilities (stable modules)
from .runtime import run_analysis
from .metrics import compute_runtime_metrics
from .analysis import analyze_apk

# Back-compat shims for renamed modules
# Prefer new names; fall back to legacy ones if the refactor isn't complete.
try:  # New name after refactor
    from .sandbox_runner import run_sandbox as _run_sandbox
except ImportError:  # Legacy name
    from .runner import run_sandbox as _run_sandbox

try:  # New name after refactor
    from .network_sniffer import sniff_network as _sniff_network
except ImportError:  # Legacy name
    from .network import sniff_network as _sniff_network

# This module name appears consistent across branches; import directly.
from .permission_monitor import collect_permissions as _collect_permissions

# Public API (assign to stable exported names)
run_sandbox = _run_sandbox
sniff_network = _sniff_network
collect_permissions = _collect_permissions

__all__ = [
    "run_analysis",
    "run_sandbox",
    "collect_permissions",
    "sniff_network",
    "compute_runtime_metrics",
    "analyze_apk",
]
