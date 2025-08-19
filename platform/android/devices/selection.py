#!/usr/bin/env python3
# selection.py
"""
Allows users to list connected devices and select one to connect to,
with numbered selection for easier navigation.
"""

from typing import Any, Dict, List, Optional

from core import display, menu
from . import discovery

_cached_devices: List[Dict[str, Any]] = []


def refresh_devices() -> List[Dict[str, Any]]:
    """Refresh and return the cached device list."""
    global _cached_devices
    _cached_devices = discovery.list_detailed_devices()
    return _cached_devices


def list_and_select_device() -> Optional[Dict[str, Any]]:
    """Display connected devices and return the chosen device dict."""
    try:
        devices = _cached_devices or refresh_devices()
        connected = [d for d in devices if d.get("state") == "device"]

        if not connected:
            display.warn("No devices attached.")
            return None

        if len(connected) == 1:
            return connected[0]

        labels = [
            f"{d.get('serial')} | {d.get('model') or '-'} | {d.get('type', '')}"
            for d in connected
        ]

        choice = menu.show_menu(
            "ADB Devices",
            labels,
            exit_label="Cancel",
            prompt="Select device",
        )

        if choice == 0:
            display.warn("No device selected.")
            return None

        return connected[choice - 1]

    except RuntimeError as e:
        display.fail(str(e))
        return None
