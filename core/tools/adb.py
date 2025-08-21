from __future__ import annotations

import shutil
import subprocess
from typing import List

from app_config import app_config


def adb_path() -> str:
    """Return the best ``adb`` path available on this system."""
    path = app_config.get_adb_path()
    which = shutil.which("adb")
    try:
        subprocess.run(
            [path, "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=True,
        )
        return path
    except Exception:
        return which or path


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
