#!/usr/bin/env python3
# device_selection.py
"""
Allows users to list connected devices and select one to connect to, 
with numbered selection for easier navigation.
"""

from app_utils import app_display, app_menu_utils
from device_analysis import device_discovery


def list_and_select_device() -> str:
    """Display connected devices and return the chosen serial."""
    try:
        devices = device_discovery.list_detailed_devices()

        if not devices:
            app_display.warn("No devices attached.")
            return ""

        labels = [
            f"{d.get('serial')} | {d.get('model') or '-'} | {d.get('state')}"
            for d in devices
        ]

        choice = app_menu_utils.show_menu(
            "ADB Devices",
            labels,
            exit_label="Cancel",
            prompt="Select device",
        )

        if choice == 0:
            app_display.warn("No device selected.")
            return ""

        selected = devices[choice - 1]
        app_display.good(f"Selected device: {selected['serial']}")

        app_display.print_section("Device Details")
        app_display.print_kv(
            [
                ("Serial", selected.get("serial", "")),
                ("Model", selected.get("model", "")),
                ("Manufacturer", selected.get("manufacturer", "")),
                ("Android", selected.get("android_release", "")),
                ("SDK", selected.get("sdk", "")),
                ("Connection", selected.get("connection", "")),
                ("Type", selected.get("type", "")),
            ]
        )

        return selected.get("serial", "")

    except RuntimeError as e:
        app_display.fail(str(e))
        return ""
