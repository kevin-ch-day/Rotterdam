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
        connected = [d for d in devices if d.get("state") == "device"]

        if not connected:
            display.warn("No devices attached.")
            return ""

        if len(connected) == 1:
            selected = connected[0]
            dtype = selected.get("type", "unknown")
            display.good(f"Selected {dtype} device: {selected['serial']}")

            display.print_section("Device Details")
            display.print_kv(
                [
                    ("Serial", selected.get("serial", "")),
                    ("Model", selected.get("model", "")),
                    ("Manufacturer", selected.get("manufacturer", "")),
                    ("Android", selected.get("android_release", "")),
                    ("SDK", selected.get("sdk", "")),
                    ("Connection", selected.get("connection", "")),
                    ("Type", dtype),
                ]
            )

            return selected.get("serial", "")

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
            return ""

        selected = connected[choice - 1]
        dtype = selected.get("type", "unknown")
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
                ("Type", dtype),
            ]
        )

        return selected.get("serial", "")

    except RuntimeError as e:
        display.fail(str(e))
        return ""
