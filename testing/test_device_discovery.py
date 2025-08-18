from device_analysis.device_discovery import parse_devices_l


def test_parse_devices_l_basic():
    output = """List of devices attached\nemulator-5554\tdevice product:sdk_gphone_x86 model:sdk_gphone_x86 device:emulator_x86 transport_id:1\nABCDEF123456\tunauthorized\n"""
    devices = parse_devices_l(output)
    assert len(devices) == 2
    first = devices[0]
    assert first["serial"] == "emulator-5554"
    assert first["product"] == "sdk_gphone_x86"
    second = devices[1]
    assert second["serial"] == "ABCDEF123456"
    assert second["state"] == "unauthorized"
