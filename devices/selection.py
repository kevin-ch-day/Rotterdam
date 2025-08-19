#!/usr/bin/env python3
# selection.py
"""
Allows users to list connected devices and select one to connect to, 
with numbered selection for easier navigation.
"""

from core import display, menu
from devices import discovery


def list_and_select_device() -> str:
    """Display connected devices and return the chosen serial."""
    try:
        devices = discovery.list_detailed_devices()

        if not devices:
            display.warn("No devices attached.")
            return ""

        labels = [
            f"{d.get('serial')} | {d.get('model') or '-'} | {d.get('state')}"
            for d in devices
        ]

        choice = menu.show_menu(
            "ADB Devices",
            labels,
            exit_label="Cancel",
            prompt="Select device",
        )

        if choice == 0:
            display.warn("No device selected.")
            return ""

        selected = devices[choice - 1]
        display.good(f"Selected device: {selected['serial']}")

        display.print_section("Device Details")
        display.print_kv(
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
        display.fail(str(e))
        return ""
