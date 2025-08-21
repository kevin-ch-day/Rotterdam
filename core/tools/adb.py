from __future__ import annotations

import subprocess
from typing import List

from settings import get_settings


def adb_path() -> str:
    """Return the resolved ``adb`` path from settings."""
    return get_settings().adb_bin


def run(args: List[str], *, timeout: int = 8) -> subprocess.CompletedProcess:
    """Run adb with robust defaults and return the completed process."""
    cmd = [adb_path(), *args]
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
    except FileNotFoundError as exc:  # pragma: no cover - external dependency
        raise RuntimeError("adb is not installed or not found in PATH") from exc
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        raise RuntimeError(f"adb failed with code {exc.returncode}") from exc


__all__ = ["run", "adb_path"]
