"""Helpers for diffing stored analysis snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set, Any


def _component_map(data: Dict[str, Any]) -> Dict[str, Set[str]]:
    comps: Dict[str, Set[str]] = {}
    for kind, items in data.get("components", {}).items():
        comps[kind] = set(items)
    return comps


def diff_snapshots(old: Path, new: Path) -> Dict[str, Any]:
    """Return added/removed permissions and components between snapshots."""
    old_data = json.loads(old.read_text())
    new_data = json.loads(new.read_text())

    old_perms = set(old_data.get("permissions", []))
    new_perms = set(new_data.get("permissions", []))
    added_perms = sorted(new_perms - old_perms)
    removed_perms = sorted(old_perms - new_perms)

    old_comps = _component_map(old_data)
    new_comps = _component_map(new_data)
    kinds = set(old_comps) | set(new_comps)
    added_comps: Dict[str, List[str]] = {}
    removed_comps: Dict[str, List[str]] = {}
    for kind in kinds:
        added = sorted(new_comps.get(kind, set()) - old_comps.get(kind, set()))
        removed = sorted(old_comps.get(kind, set()) - new_comps.get(kind, set()))
        if added:
            added_comps[kind] = added
        if removed:
            removed_comps[kind] = removed

    return {
        "added_permissions": added_perms,
        "removed_permissions": removed_perms,
        "added_components": added_comps,
        "removed_components": removed_comps,
    }
