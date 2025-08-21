from __future__ import annotations

from pathlib import Path

from core.tools import apktool as _apktool


def decompile(apk: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    _apktool.run(["d", str(apk), "-o", str(out_dir)])
    return out_dir

__all__ = ["decompile"]
