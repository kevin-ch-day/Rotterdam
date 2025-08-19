from __future__ import annotations

"""Diagnostic helpers for verifying environment dependencies.

These classes are used by the CLI "doctor" command to audit required
binaries and Python modules.  The design is intentionally modular so
additional checks can be added in the future.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Iterable, List
import importlib
from shutil import which


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    category: str
    name: str
    ok: bool
    detail: str

    @property
    def flag(self) -> bool:
        """Whether this result indicates a problem."""
        return not self.ok


class BaseCheck(ABC):
    """Abstract base class for diagnostic checks."""

    category: str
    name: str

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute the check and return a :class:`CheckResult`."""
        raise NotImplementedError


class BinaryCheck(BaseCheck):
    """Verify that an external binary exists on the ``PATH``."""

    category = "binary"

    def __init__(self, command: str):
        self.name = command

    def run(self) -> CheckResult:  # pragma: no cover - wrapper over shutil.which
        path = which(self.name)
        if path:
            return CheckResult(self.category, self.name, True, path)
        return CheckResult(self.category, self.name, False, "not found")


class ModuleCheck(BaseCheck):
    """Verify that a Python module can be imported."""

    category = "module"

    def __init__(self, module: str):
        self.name = module

    def run(self) -> CheckResult:  # pragma: no cover - import side effects
        try:
            mod = importlib.import_module(self.name)
        except Exception as exc:
            return CheckResult(self.category, self.name, False, str(exc))
        version = getattr(mod, "__version__", "ok")
        return CheckResult(self.category, self.name, True, str(version))


class SystemDoctor:
    """Coordinate execution of a series of diagnostic checks."""

    def __init__(self, checks: Iterable[BaseCheck]):
        self.checks: List[BaseCheck] = list(checks)
        self.results: List[CheckResult] = []

    def run(self) -> List[CheckResult]:
        """Run all registered checks and return their results."""
        self.results = [chk.run() for chk in self.checks]
        return self.results

    @property
    def has_issues(self) -> bool:
        """Return ``True`` if any check failed."""
        return any(r.flag for r in self.results)

    def failed(self) -> List[CheckResult]:
        """Return a list of failed checks."""
        return [r for r in self.results if r.flag]
