from __future__ import annotations

import sys

# If the standard library ``platform`` module was imported earlier, remove it so
# that our local ``platform`` package (which exposes Android helpers) can be
# loaded instead.
if "platform" in sys.modules and not hasattr(sys.modules["platform"], "__path__"):
    del sys.modules["platform"]

from platform.android.devices import (
    adb,
    apk,
    discovery,
    packages,
    processes,
    props,
    selection,
)

from . import service
from .types import DeviceInfo

__all__ = [
    "adb",
    "apk",
    "discovery",
    "packages",
    "processes",
    "props",
    "selection",
    "service",
    "DeviceInfo",
]
