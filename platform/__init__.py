"""Compatibility wrapper around Python's ``platform`` module.

This package exposes the repository's platform-specific subpackages while
re-exporting all public attributes from the standard library ``platform``
module so third-party imports continue to function.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

# Load the stdlib platform module under a temporary name
_stdlib_path = (
    Path(sys.base_prefix)
    / f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    / "platform.py"
)
_loader = importlib.machinery.SourceFileLoader("_stdlib_platform", str(_stdlib_path))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
_stdlib_platform = importlib.util.module_from_spec(_spec)
_loader.exec_module(_stdlib_platform)

# Re-export public attributes
for _name in dir(_stdlib_platform):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_stdlib_platform, _name)

__all__ = [name for name in globals() if not name.startswith("_")]
