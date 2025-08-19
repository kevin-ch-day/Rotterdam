#!/usr/bin/env python3
"""Utility to monitor Android runtime permission accesses via ``adb``.

This module hooks into ``adb shell dumpsys appops`` (or ``appops`` directly)
output to watch for runtime permission checks while an application is
running. Each permission access is logged with a timestamp and the calling
component. A summary of the observed accesses can be retrieved for report
generation.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import DefaultDict, Dict, Iterable, List

from devices import adb
from logging_config import get_logger, log_context

logger = get_logger(__name__)


def collect_permissions(apk_path: str) -> List[str]:
    """Stub collecting of runtime permissions for *apk_path*.

    This simplified implementation returns a fixed permission list suitable
    for tests without requiring an attached device.
    """
    return ["android.permission.INTERNET"]


def _run_shell(cmd: list[str]) -> str:
    """Run ``adb shell`` with *cmd* and return stdout as text."""
    adb_path = adb._adb_path()
    proc = adb._run_adb([adb_path, "shell", *cmd])
    return proc.stdout


def collect_permissions(apk_path: str) -> List[str]:
    """Return a mocked list of permissions requested by *apk_path*.

    This helper is a lightweight stand-in for a real APK parser. It simply
    returns a few common permissions so higher-level utilities and tests can
    exercise expected workflows without requiring the Android tooling.
    """

    return [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
    ]


class PermissionMonitor:
    """Monitor permission accesses for a device or specific package."""

    def __init__(self, package: str | None = None, *, use_dumpsys: bool = True):
        self.package = package
        self.use_dumpsys = use_dumpsys
        self._summary: DefaultDict[str, int] = defaultdict(int)
        self._logs: List[PermissionAccess] = []

    def poll(self) -> None:
        """Poll ``appops`` and update internal summary and logs."""
        if self.use_dumpsys:
            cmd = ["dumpsys", "appops"]
        else:
            cmd = ["appops", "get"]
            if self.package:
                cmd.append(self.package)
        output = _run_shell(cmd)
        self._parse_output(output)

    def _parse_output(self, output: str) -> None:
        pattern = re.compile(
            r"Op\s+(?P<perm>[A-Z_\.]+).*?from uid\s+\d+\s+pkg\s+(?P<comp>[\w\.]+)"
        )
        for line in output.splitlines():
            line = line.strip()
            match = pattern.search(line)
            if not match:
                continue
            perm = match.group("perm")
            comp = match.group("comp")
            timestamp = datetime.now(tz=timezone.utc).isoformat()
            access = PermissionAccess(timestamp, perm, comp)
            with log_context(app=self.package):
                logger.info("%s | %s accessed by %s", timestamp, perm, comp)
            self._summary[perm] += 1
            self._logs.append(access)

    def get_summary(self) -> Dict[str, int]:
        """Return a ``{permission: count}`` summary of logged accesses."""
        return dict(self._summary)

    def get_logs(self) -> Iterable["PermissionAccess"]:
        """Return an iterable of logged permission accesses."""
        return list(self._logs)

    def clear(self) -> None:
        """Clear stored logs and summary counts."""
        self._summary.clear()
        self._logs.clear()


@dataclass
class PermissionAccess:
    """Structured record describing a single permission access."""

    timestamp: str
    permission: str
    component: str


__all__ = ["collect_permissions", "PermissionMonitor", "PermissionAccess"]
