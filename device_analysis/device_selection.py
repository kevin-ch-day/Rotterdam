#!/usr/bin/env python3
# device_selection.py
"""
Allows users to list connected devices and select one to connect to, 
with numbered selection for easier navigation.
"""

from app_utils import app_display
from device_analysis import device_discovery


def list_and_select_device() -> str:
    """
    Lists all connected devices and lets the user select one by number.
    Returns the serial number of the selected device.
    """
    try:
        # Get the list of devices
        devices = device_discovery.list_detailed_devices()

        # If no devices are connected
        if not devices:
            app_display.warn("No devices attached.")
            return ""

        # Display the list of devices in a numbered menu format
        app_display.print_section("ADB Devices")
        for index, device in enumerate(devices, start=1):
            print(f"[{index}] Serial: {device['serial']} | Model: {device['model']} | State: {device['state']}")

        # Ask user to select a device
        try:
            selection = int(input("\nSelect the device by number: ").strip())
            if selection < 1 or selection > len(devices):
                app_display.fail("Invalid selection, please choose a valid number.")
                return ""

            selected_device = devices[selection - 1]
            app_display.good(f"Selected device: {selected_device['serial']}")
            return selected_device['serial']

        except ValueError:
            app_display.fail("Invalid input, please enter a number.")
            return ""

    except RuntimeError as e:
        app_display.fail(str(e))
        return ""
