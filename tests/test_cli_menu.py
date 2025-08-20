import importlib
import sys
import types

from core import menu as core_menu
from core import config, display


def test_run_main_menu_launches_web_app(monkeypatch):
    # Prepare stub modules to avoid heavy imports
    actions_stub = types.ModuleType("cli.actions")
    launch_called = {"called": False}
    actions_stub.show_connected_devices = lambda: None
    actions_stub.show_detailed_devices = lambda: None
    actions_stub.scan_for_devices = lambda: None
    actions_stub.launch_web_app = lambda *a, **k: launch_called.__setitem__("called", True)
    sys.modules["cli.actions"] = actions_stub

    selection_stub = types.ModuleType("devices.selection")
    selection_stub.list_and_select_device = lambda: None
    sys.modules["devices.selection"] = selection_stub

    choices = [5, 0]
    monkeypatch.setattr(core_menu, "show_menu", lambda *a, **k: choices.pop(0))
    monkeypatch.setattr(config, "ensure_dirs", lambda: None)
    monkeypatch.setattr(display, "print_app_banner", lambda *a, **k: None)

    cli_menu = importlib.import_module("cli.menu")
    cli_menu.run_main_menu()

    assert launch_called["called"]
