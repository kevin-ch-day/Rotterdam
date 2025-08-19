from core.helpers import truncate_middle
from devices.discovery import parse_devices_l


def test_truncate_middle():
    assert truncate_middle("abcdefghijklmnopqrstuvwxyz", 10) == "abcd…vwxyz"


def test_parse_devices_l():
    raw = "List of devices attached\nABC123\tdevice usb:1-2 transport_id:5"
    devices = parse_devices_l(raw)
    assert len(devices) == 1
    d = devices[0]
    assert d["serial"] == "ABC123"
    assert d["state"] == "device"
    assert d["usb"] == "1-2"
    assert d["transport_id"] == "5"
