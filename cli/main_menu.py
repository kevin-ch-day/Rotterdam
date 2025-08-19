"""Main menu loop for the Android Tool CLI."""

from __future__ import annotations

from app_utils import app_config, app_display, app_menu_utils
from device_analysis import device_selection

from . import device_actions


def _ensure_device_selected(serial: str) -> bool:
    """Return True if a device serial is provided, else warn the user."""
    if not serial:
        app_display.warn("No device selected. Use option 2 first.")
        return False
    return True


def run_main_menu() -> None:
    """Launch the interactive main menu."""
    # Ensure required directories exist
    app_config.ensure_dirs()

    # App banner
    app_display.print_app_banner()

    selected_serial = ""

    def handle_choice(choice: int, label: str) -> None:
        nonlocal selected_serial
        if choice == 1:
            device_actions.show_connected_devices()
        elif choice == 2:
            selected_serial = device_selection.list_and_select_device() or ""
        elif choice == 3:
            device_actions.show_detailed_devices()
        elif choice == 4:
            if _ensure_device_selected(selected_serial):
                device_actions.list_installed_packages(selected_serial)
        elif choice == 5:
            if _ensure_device_selected(selected_serial):
                device_actions.scan_dangerous_permissions(selected_serial)
        elif choice == 6:
            if _ensure_device_selected(selected_serial):
                device_actions.list_running_processes(selected_serial)
        elif choice == 7:
            device_actions.analyze_apk_path()
        elif choice == 8:
            if _ensure_device_selected(selected_serial):
                device_actions.analyze_installed_app(selected_serial)
        elif choice == 9:
            device_actions.sandbox_analyze_apk()
        else:
            app_display.warn(f"Unhandled choice: {choice}")

    app_menu_utils.run_menu_loop(
        "Main Menu\n--------------------------------",
        [
            "Check for connected devices",
            "Connect to a device",
            "List detailed devices",
            "List installed packages on selected device",
            "Scan installed apps for dangerous permissions",
            "List running processes on selected device",
            "Analyze a local APK for permissions and secrets",
            "Pull and analyze an installed app",
            "Sandbox analyze a local APK",
        ],
        handler=handle_choice,
        exit_label="Exit App",
    )

    app_display.good("Exiting App")
