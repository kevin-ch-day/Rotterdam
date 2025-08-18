"""Simple static analysis utilities for APK files."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List
import json

# Regex patterns for permissions and possible secrets
PERM_PATTERN = re.compile(r"android.permission.[A-Z0-9_]+")
SECRET_PATTERN = re.compile(r"API[_-]?KEY|SECRET|TOKEN", re.IGNORECASE)


def extract_permissions(manifest_text: str) -> List[str]:
    """Return unique permission strings from an AndroidManifest.xml text."""
    return sorted(set(PERM_PATTERN.findall(manifest_text)))


def scan_for_secrets(root: Path) -> List[str]:
    """Scan a directory tree for common secret keywords.

    Returns a list of "path:offset" strings for each finding.
    """
    findings: List[str] = []
    for file in root.rglob("*"):
        if not file.is_file():
            continue
        try:
            text = file.read_text(errors="ignore")
        except Exception:
            continue
        for match in SECRET_PATTERN.finditer(text):
            rel = file.relative_to(root)
            findings.append(f"{rel}:{match.start()}")
    return findings


def analyze_apk(apk_path: str, outdir: str = "analysis") -> Path:
    """Decompile an APK and scan for permissions and secrets.

    Returns the output directory used for analysis.
    """
    apk = Path(apk_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    apktool_dir = out / "apktool"
    jadx_dir = out / "jadx"

    subprocess.run([
        "apktool",
        "d",
        str(apk),
        "-o",
        str(apktool_dir),
    ], check=True, stdout=subprocess.DEVNULL)

    subprocess.run([
        "jadx",
        "-d",
        str(jadx_dir),
        str(apk),
    ], check=True, stdout=subprocess.DEVNULL)

    manifest = apktool_dir / "AndroidManifest.xml"
    perms: List[str] = []
    if manifest.exists():
        perms = extract_permissions(manifest.read_text())
        (out / "permissions.txt").write_text("\n".join(perms))

    secrets = scan_for_secrets(jadx_dir)
    if secrets:
        (out / "secrets.txt").write_text("\n".join(secrets))

    write_report(out, perms, secrets)

    return out


def write_report(out: Path, permissions: List[str], secrets: List[str]) -> Path:
    """Write a JSON report containing permissions and secrets."""
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps({"permissions": permissions, "secrets": secrets}, indent=2)
    )
    return report_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m apk_analysis.apk_static <apk> [output_dir]")
        raise SystemExit(1)

    apk_file = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else "analysis"
    analyze_apk(apk_file, dest)

