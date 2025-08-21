from __future__ import annotations

import subprocess
from typing import Sequence


def run(args: Sequence[str], *, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run the ``androguard`` command with the given arguments."""
    cmd = ["androguard", *args]
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
    except FileNotFoundError as exc:  # pragma: no cover - external dependency
        raise RuntimeError("androguard is not installed or not found in PATH") from exc
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        raise RuntimeError(f"androguard failed with code {exc.returncode}") from exc


__all__ = ["run"]
