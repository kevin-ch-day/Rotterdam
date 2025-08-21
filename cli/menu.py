"""CLI menus for the Android Tool."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app_config import app_config
from devices import adb, selection
from utils.display_utils import display

from . import actions


def device_online(serial: str) -> bool:
    """Return True if the device is online according to ``adb get-state``."""
    if not serial:
        return False
    adb_path = adb._adb_path()
    try:
        proc = adb._run_adb([adb_path, "-s", serial, "get-state"])
    except Exception:
        return False
    return (proc.stdout or "").strip() == "device"


def run_device_menu(serial: str, *, json_mode: bool = False) -> Optional[str | Dict[str, Any]]:
    """Launch the device submenu for a selected device."""
    if not serial:
        display.warn("No device serial provided.")
        return None

    options = [
        "List installed packages",
        "Scan installed apps for dangerous permissions",
        "List running processes",
        "Analyze a local APK (static)",
        "Pull and analyze an installed app",
        "Sandbox analyze a local APK",
        "Explore installed app UI",
    ]

    if json_mode:
        return {
            "title": "Device Menu",
            "serial": serial,
            "options": [{"key": str(i + 1), "label": opt} for i, opt in enumerate(options)],
            "exit": "Back",
        }

    if not device_online(serial):
        display.warn(f"Device {serial} is no longer online.")
        return None

    # Accept 0..len(options) and 'q' for quit
    valid = {str(i) for i in range(len(options) + 1)}
    valid.add("q")

    while True:
        if not device_online(serial):
            display.warn(f"Device {serial} is no longer online.")
            return None

        print()
        print(
            display.render_menu(
                "Device Menu",
                options,
                exit_label="Back",
                serial=serial,
            )
        )

        choice = display.prompt_choice(valid, message="Select option")
        if choice == "q":
            return "quit"
        if choice == "0":
            return None

        if not device_online(serial):
            display.warn(f"Device {serial} is no longer online.")
            return None

        num = int(choice)
        if num == 1:
            actions.list_installed_packages(serial)
        elif num == 2:
            actions.scan_dangerous_permissions(serial)
        elif num == 3:
            actions.list_running_processes(serial)
        elif num == 4:
            actions.analyze_apk_path()
        elif num == 5:
            actions.analyze_installed_app(serial)
        elif num == 6:
            actions.sandbox_analyze_apk()
        elif num == 7:
            actions.explore_installed_app(serial)
        else:  # pragma: no cover - defensive
            display.warn("Invalid choice. Please try again.")


def run_main_menu(*, json_mode: bool = False) -> Optional[Dict[str, Any]]:
    """Launch the interactive main menu."""

    options = [
        "Check for connected devices",
        "List detailed devices",
        "Scan for devices",
        "Connect to a device",
        "Launch Web app",
        "Check Application Status",
        "Database",
        "About Application",
    ]

    if json_mode:
        return {
            "title": "Main Menu",
            "options": [{"key": str(i + 1), "label": opt} for i, opt in enumerate(options)],
            "exit": "Exit",
        }

    # Ensure required directories exist
    app_config.ensure_dirs()

    # App banner
    display.print_app_banner()

    while True:
        num = display.show_menu("Main Menu", options, exit_label="Exit")
        if num == 0:
            display.ok("Exiting App")
            return None

        if num == 1:
            actions.show_connected_devices()
        elif num == 2:
            actions.show_detailed_devices()
        elif num == 3:
            actions.scan_for_devices()
        elif num == 4:
            device = selection.list_and_select_device()
            if device:
                display.print_section("Device Summary")
                display.print_kv(
                    [
                        ("Serial", device.serial),
                        ("Model", device.model),
                        ("Android", device.android_release),
                    ]
                )
                result = run_device_menu(device.serial)
                if result == "quit":
                    display.ok("Exiting App")
                    return None
        elif num == 5:
            actions.launch_web_app()
        elif num == 6:
            display.info("Application status check not implemented yet.")
        elif num == 7:
            display.info("Database feature not implemented yet.")
        elif num == 8:
            display.info("About information not implemented yet.")
        else:  # pragma: no cover - defensive
            display.warn("Invalid choice. Please try again.")


__all__ = ["run_main_menu", "run_device_menu"]
