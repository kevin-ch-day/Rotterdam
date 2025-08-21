from __future__ import annotations

import shutil
import subprocess
from typing import List

from app_config import app_config


def _resolve_adb() -> str:
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


def _raw(args: List[str], *, timeout: int) -> subprocess.CompletedProcess:
    cmd = [_resolve_adb(), *args]
    return subprocess.run(
        cmd, capture_output=True, text=True, check=True, timeout=timeout
    )


def run(args: List[str], *, timeout: int = 8, _retry: bool = True) -> subprocess.CompletedProcess:
    """Run adb with retries and human-readable errors."""
    try:
        return _raw(args, timeout=timeout)
    except FileNotFoundError as exc:  # pragma: no cover - external dep
        raise RuntimeError("adb is not installed or not found in PATH") from exc
    except PermissionError as exc:  # pragma: no cover - external dep
        raise RuntimeError("adb is not executable (check permissions)") from exc
    except subprocess.CalledProcessError as exc:
        if _retry:
            try:
                _raw(["kill-server"], timeout=timeout)
                _raw(["start-server"], timeout=timeout)
            except Exception:
                pass
            return run(args, timeout=timeout, _retry=False)
        raise RuntimeError(
            f"adb failed with code {exc.returncode}: {exc.stderr.strip()}"
        ) from exc


__all__ = ["run"]
