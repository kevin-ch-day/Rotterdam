from __future__ import annotations

import importlib
import shutil
import subprocess
from typing import List

from settings import get_settings
from utils.display_utils import display
from database.db_core import DatabaseCore
from database.db_config import DB_CONFIG


def _check_adb() -> tuple[bool, str]:
    path = get_settings().adb_bin
    try:
        proc = subprocess.run(
            [path, "version"], capture_output=True, text=True, timeout=2, check=True
        )
        line = (proc.stdout or "").splitlines()[0].strip()
        return True, line or path
    except Exception:
        hint = f"adb missing (looked for {path}). Install platform-tools or set ADB env"
        return False, hint


def _check_module(name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(name)
        return True, "ok"
    except Exception as e:  # pragma: no cover - import error path
        return False, str(e)


def _check_binary(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    if path:
        return True, path
    return False, f"{name} not found in PATH"


def _check_database() -> tuple[bool, str]:
    core = DatabaseCore(DB_CONFIG)
    ok = core.ping()
    return ok, "connected" if ok else "unreachable"


def run_health_check() -> None:
    """Run read-only environment diagnostics."""
    display.print_section("Health Check")
    checks: List[tuple[str, tuple[bool, str]]] = [
        ("ADB", _check_adb()),
        ("androguard", _check_module("androguard")),
        ("apktool", _check_binary("apktool")),
        ("database", _check_database()),
    ]
    for name, (ok, detail) in checks:
        if ok:
            display.ok(f"{name}: {detail}")
        else:
            display.fail(f"{name}: {detail}")


__all__ = ["run_health_check"]
