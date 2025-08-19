from __future__ import annotations

import subprocess
from typing import Sequence

from core import display


def run_tool(cmd: Sequence[str], tool_name: str) -> None:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        display.fail(f"{tool_name} is not installed or not found in PATH")
        raise RuntimeError(f"{tool_name} missing") from None
    except subprocess.CalledProcessError as e:
        display.fail(f"{tool_name} failed: {e}")
        raise RuntimeError(f"{tool_name} execution failed") from e

__all__ = ["run_tool"]
