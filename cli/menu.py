"""Main menu loop for the Android Tool CLI."""

from __future__ import annotations

from core import config, display, menu
from devices import selection

from . import actions


def _ensure_device_selected(serial: str) -> str:
    """Return a device serial, prompting the user if needed."""
    if serial:
        return serial
    display.warn("No device selected.")
    return selection.list_and_select_device() or ""


def run_main_menu() -> None:
    """Launch the interactive main menu."""
    # Ensure required directories exist
    config.ensure_dirs()

    # App banner
    display.print_app_banner()

    selected_serial = ""

    options = [
        "Check for connected devices",
        "Connect to a device",
        "List detailed devices",
        "List installed packages on selected device",
        "Scan installed apps for dangerous permissions",
        "Check Application Status",
        "List running processes on selected device",
        "Analyze a local APK for permissions and secrets",
        "Pull and analyze an installed app",
        "Sandbox analyze a local APK",
        "Explore installed app UI",
    ]

    class _RefreshMenu(Exception):
        """Internal exception used to refresh the menu title."""

    def handle_choice(choice: int, label: str) -> None:
        nonlocal selected_serial
        if choice == 1:
            actions.show_connected_devices()
        elif choice == 2:
            selected_serial = selection.list_and_select_device() or ""
        elif choice == 3:
            actions.show_detailed_devices()
        elif choice == 4:
            selected_serial = _ensure_device_selected(selected_serial)
            if selected_serial:
                actions.list_installed_packages(selected_serial)
        elif choice == 5:
            selected_serial = _ensure_device_selected(selected_serial)
            if selected_serial:
                actions.scan_dangerous_permissions(selected_serial)
        elif choice == 6:
            actions.run_doctor()
        elif choice == 7:
            selected_serial = _ensure_device_selected(selected_serial)
            if selected_serial:
                actions.list_running_processes(selected_serial)
        elif choice == 8:
            actions.analyze_apk_path()
        elif choice == 9:
            selected_serial = _ensure_device_selected(selected_serial)
            if selected_serial:
                actions.analyze_installed_app(selected_serial)
        elif choice == 10:
            actions.sandbox_analyze_apk()
        elif choice == 11:
            selected_serial = _ensure_device_selected(selected_serial)
            if selected_serial:
                actions.explore_installed_app(selected_serial)
        else:
            display.warn(f"Unhandled choice: {choice}")
        raise _RefreshMenu

    while True:
        current = selected_serial or "None"
        try:
            menu.run_menu_loop(
                f"Main Menu — Device: {current}\n--------------------------------",
                options,
                handler=handle_choice,
                exit_label="Exit App",
            )
            break
        except _RefreshMenu:
            continue

    display.good("Exiting App")
