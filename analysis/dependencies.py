"""Extract dependency information from APKs and flag CVE matches.

This module provides helpers to parse an APK for dependency names and
versions and cross-reference them against a local CVE database such as the
NVD JSON feed.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

# Regular expression to extract library names and optional versions from
# native ``.so`` filenames.  Matches patterns like ``libfoo.so`` or
# ``libfoo-1.2.3.so``.
LIB_PATTERN = re.compile(
    r"lib(?P<name>[A-Za-z0-9_\-]+?)(?:-(?P<version>[0-9][A-Za-z0-9.\-]*))?\.so$"
)


def parse_apk_dependencies(apk_path: str) -> List[Dict[str, str | None]]:
    """Return dependency names and versions referenced by an APK.

    The function inspects the APK's ``lib`` directory for native libraries and
    scans ``classes.dex`` for package references.  Versions are heuristically
    extracted from library filenames when present.
    """

    deps: List[Dict[str, str | None]] = []
    with zipfile.ZipFile(apk_path) as apk:
        # Native libraries under lib/<abi>/
        for name in apk.namelist():
            if not name.startswith("lib/") or not name.endswith(".so"):
                continue
            match = LIB_PATTERN.search(Path(name).name)
            if match:
                deps.append(
                    {
                        "name": match.group("name"),
                        "version": match.group("version"),
                    }
                )

        # Scan classes.dex for package references
        if "classes.dex" in apk.namelist():
            dex_data = apk.read("classes.dex")
            packages = set()
            for m in re.findall(rb"L([a-zA-Z0-9_/]+);", dex_data):
                pkg = m.decode(errors="ignore").replace("/", ".")
                parts = pkg.split(".")
                if len(parts) > 1:
                    packages.add(".".join(parts[:-1]))
            for pkg in sorted(packages):
                deps.append({"name": pkg, "version": None})
    return deps


def load_cve_db(path: str) -> List[Dict[str, Any]]:
    """Load CVE entries from a JSON database.

    The function understands the structure of the NVD JSON feed and returns a
    list of dictionaries with ``id``, ``product`` and ``version`` keys.
    """

    data = json.loads(Path(path).read_text())
    items = data.get("CVE_Items", []) if isinstance(data, dict) else data
    cves: List[Dict[str, Any]] = []
    for item in items:
        cve_id = item.get("cve", {}).get("CVE_data_meta", {}).get("ID")
        nodes = item.get("configurations", {}).get("nodes", [])
        for node in nodes:
            for match in node.get("cpe_match", []):
                uri = match.get("cpe23Uri", "")
                parts = uri.split(":")
                if len(parts) >= 6:
                    product = parts[4]
                    version = parts[5]
                    cves.append({"id": cve_id, "product": product, "version": version})
    return cves


def find_vulnerable_dependencies(
    deps: Iterable[Dict[str, str | None]],
    cves: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return dependencies that match known CVE entries.

    A dependency is considered vulnerable when the name contains the CVE's
    product string and the versions match (if both specify a version).
    """

    vulns: List[Dict[str, Any]] = []
    for dep in deps:
        name = (dep.get("name") or "").lower()
        version = dep.get("version")
        for cve in cves:
            product = cve.get("product", "").lower()
            cve_version = cve.get("version")
            if product and product in name:
                if version is None or cve_version in {"*", version}:
                    entry = {**dep, "cve": cve.get("id")}
                    vulns.append(entry)
                    break
    return vulns


def analyze_dependencies(apk_path: str, cve_db_path: str) -> Dict[str, Any]:
    """Convenience wrapper returning dependency and vulnerability info."""
    deps = parse_apk_dependencies(apk_path)
    cves = load_cve_db(cve_db_path)
    vulns = find_vulnerable_dependencies(deps, cves)
    return {
        "dependencies": deps,
        "vulnerabilities": vulns,
        "vulnerable_dependency_count": len(vulns),
    }
