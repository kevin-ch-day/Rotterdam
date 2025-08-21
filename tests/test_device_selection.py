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


def test_refresh_devices_returns_deviceinfo(monkeypatch):
    _install_devices_stub(monkeypatch)
    from rotterdam.android.devices import selection

    from devices.types import DeviceInfo

    sample = [
        {
            "serial": "abc123",
            "state": "device",
            "product": "prod",
            "model": "mod",
            "device": "dev",
            "transport_id": "1",
            "type": "usb",
        }
    ]

    monkeypatch.setattr(selection.discovery, "list_detailed_devices", lambda: sample)
    devices = selection.refresh_devices()
    assert len(devices) == 1
    dev = devices[0]
    assert isinstance(dev, DeviceInfo)
    assert dev.serial == "abc123"
    assert dev.model == "mod"
