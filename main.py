#!/usr/bin/env python3
# main.py
"""
Entry point for Android Tool CLI.
Initializes config, shows banner, and launches the main menu.
"""

from app_utils import app_config, app_menu_utils, app_display
from device_analysis import device_discovery, device_selection


def main() -> None:
    # Ensure required directories exist
    app_config.ensure_dirs()

    # App banner
    app_display.print_app_banner()

    # Menu handler
    def handle_choice(choice: int, label: str) -> None:
        if choice == 1:
            try:
                output = device_discovery.check_connected_devices()
                devs = device_discovery.parse_devices_l(output)

                app_display.print_section("ADB Devices")

                if not devs:
                    print("No devices attached.")
                    return

                rows = [
                    [
                        d.get("serial", ""),
                        d.get("state", ""),
                        d.get("product", "-"),
                        d.get("model", "-"),
                        d.get("device", "-"),
                        d.get("transport_id", "-"),
                    ]
                    for d in devs
                ]
                app_display.print_table(
                    rows,
                    headers=["Serial", "State", "Product", "Model", "Device", "Transport"],
                )
            except RuntimeError as e:
                app_display.fail(str(e))

        elif choice == 2:
            # Use the new function to list and select a device
            selected_device = device_selection.list_and_select_device()

            if selected_device:
                app_display.good(f"Device {selected_device} connected successfully.")
                # Store the selected device for further usage if needed (e.g., set it in a config or in-memory)

        elif choice == 3:
            app_display.info("Other features (to be implemented)")

        else:
            app_display.warn(f"Unhandled choice: {choice}")

    # Main loop
    app_menu_utils.run_menu_loop(
        "Main Menu\n--------------------------------",
        ["Check for connected devices", "Connect to a device", "Other"],
        handler=handle_choice,
        exit_label="Exit App",
    )

    app_display.good("Exiting App")


if __name__ == "__main__":
    main()
