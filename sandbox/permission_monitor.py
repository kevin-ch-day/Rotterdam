"""Facade for permission monitoring utilities.

This module wraps select helpers from
:mod:`android.analysis.dynamic.permission_monitor` so that tests can
patch internal helpers like :func:`_run_shell`.
"""
from __future__ import annotations

import android.analysis.dynamic.permission_monitor as _impl
from android.analysis.dynamic.permission_monitor import PermissionAccess


def _run_shell(cmd: list[str]) -> str:
    """Delegate to the underlying implementation's shell runner."""
    return _impl._run_shell(cmd)


class PermissionMonitor(_impl.PermissionMonitor):
    """Proxy that routes shell calls through this module for easy patching."""

    def poll(self) -> None:  # type: ignore[override]
        if self.use_dumpsys:
            cmd = ["dumpsys", "appops"]
        else:
            cmd = ["appops", "get"]
            if self.package:
                cmd.append(self.package)
        output = _run_shell(cmd)
        self._parse_output(output)


def collect_permissions(apk_path: str) -> list[str]:
    """Return a list of permissions requested by ``apk_path``."""
    return _impl.collect_permissions(apk_path)


__all__ = ["collect_permissions"]

