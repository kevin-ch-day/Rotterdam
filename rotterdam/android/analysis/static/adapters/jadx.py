from __future__ import annotations

from pathlib import Path

from .common import run_tool


def decompile(apk: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_tool(["jadx", "-d", str(out_dir), str(apk)], "jadx")
    return out_dir

__all__ = ["decompile"]
