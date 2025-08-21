#!/usr/bin/env python3
# File: platform/android/devices/selection.py
# selection.py
"""
Allows users to list connected devices and select one to connect to,
with numbered selection for easier navigation.
"""

from typing import List, Optional

from devices.types import DeviceInfo
from utils.display_utils import display

from . import discovery

_cached_devices: List[DeviceInfo] = []


def refresh_devices() -> List[DeviceInfo]:
    """Refresh and return the cached device list."""
    global _cached_devices
    _cached_devices = [DeviceInfo(**d) for d in discovery.list_detailed_devices()]
    return _cached_devices


def list_and_select_device() -> Optional[DeviceInfo]:
    """Display connected devices and return the chosen device."""
    try:
        devices = _cached_devices or refresh_devices()
        connected = [d for d in devices if d.state == "device"]

        if not connected:
            display.warn("No devices attached.")
            return None

        if len(connected) == 1:
            return connected[0]

        labels = [f"{d.serial} | {d.model or '-'} | {d.type}" for d in connected]

        choice = display.show_menu(
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
