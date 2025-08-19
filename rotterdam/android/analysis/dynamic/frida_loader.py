"""Utilities for discovering and selecting Frida hook scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def discover_scripts(scripts_dir: Path | None = None) -> List[str]:
    """Return a sorted list of available hook script names without extension."""
    scripts_dir = scripts_dir or Path(__file__).with_name("frida_scripts")
    return sorted(p.stem for p in scripts_dir.glob("*.js"))


def resolve_hooks(
    enabled: Iterable[str] | None = None,
    disabled: Iterable[str] | None = None,
    scripts_dir: Path | None = None,
) -> List[str]:
    """Determine which hooks to load based on enabled/disabled lists."""
    available = set(discover_scripts(scripts_dir))
    hooks = set(enabled) if enabled is not None else set(available)
    hooks &= available  # ensure all exist
    if disabled:
        hooks.difference_update(disabled)
    return sorted(hooks)
