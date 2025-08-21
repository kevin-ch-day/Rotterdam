import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _install_devices_stub(monkeypatch):
    spec = importlib.util.spec_from_file_location("devices.types", ROOT / "devices" / "types.py")
    device_types = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "devices.types", device_types)
    spec.loader.exec_module(device_types)
    fake_devices = types.ModuleType("devices")
    fake_devices.types = device_types
    monkeypatch.setitem(sys.modules, "devices", fake_devices)
    return device_types


def test_format_device_inventory_import(monkeypatch):
    _install_devices_stub(monkeypatch)
    from devices.types import DeviceInfo
    from utils.reporting_utils import ieee

    dev = DeviceInfo(serial="xyz", state="device")
    table = ieee.format_device_inventory([dev])
    assert "Serial" in table
    assert "xyz" in table
