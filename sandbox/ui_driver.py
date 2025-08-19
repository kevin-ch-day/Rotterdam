from __future__ import annotations

"""Automated UI exploration helpers using ``adb shell monkey``."""

import re
import subprocess
from typing import List, Sequence, Set

_ACTIVITY_CMP_RE = re.compile(r"cmp=([\w./$-]+)")
_ACTIVITY_GENERIC_RE = re.compile(r"Activity\s*: ?([\w./$-]+)")


def _parse_monkey_output(output: str, package: str) -> List[str]:
    """Extract visited activities from monkey output.

    Parameters
    ----------
    output:
        Raw stdout/stderr combined output from the monkey process.
    package:
        Application package name. Used to resolve relative activity names and
        filter out unrelated components.

    Returns
    -------
    List[str]
        Sorted list of unique activity names encountered during the run.
    """
    visited: Set[str] = set()
    for line in output.splitlines():
        match = _ACTIVITY_CMP_RE.search(line) or _ACTIVITY_GENERIC_RE.search(line)
        if not match:
            continue
        component = match.group(1)
        if component.startswith("." ):
            component = package + component
        if package and not component.startswith(package):
            continue
        visited.add(component)
    return sorted(visited)


def run_monkey(
    serial: str,
    package: str,
    event_count: int = 1000,
    extra_args: Sequence[str] | None = None,
) -> List[str]:
    """Drive the target app using Android's ``monkey`` tool.

    This function invokes ``adb shell monkey`` for the specified package and
    parses the output to determine which activities were visited.  The list of
    unique activities is returned so that callers can incorporate coverage
    metrics into reports.
    """
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += ["shell", "monkey", "-p", package, "-v"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(str(event_count))

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return _parse_monkey_output(proc.stdout, package)


__all__ = ["run_monkey"]
