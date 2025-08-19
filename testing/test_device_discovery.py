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


def test_list_detailed_devices_trust(monkeypatch):
    import device_analysis.device_discovery as dd

    # Fake device list with one online device
    monkeypatch.setattr(dd, "check_connected_devices", lambda: "ignored")
    monkeypatch.setattr(dd, "parse_devices_l", lambda out: [{"serial": "SER", "state": "device"}])

    # Provide properties indicating a developer/rooted build
    def fake_props(serial):
        return {
            "ro.product.manufacturer": "Acme",
            "ro.product.model": "Model",
            "ro.build.version.release": "11",
            "ro.build.version.sdk": "30",
            "ro.product.cpu.abi": "arm64-v8a",
            "ro.board.platform": "",
            "ro.hardware": "",
            "ro.boot.qemu": "",
            "ro.build.fingerprint": "acme/model:test-keys",
            "ro.build.tags": "test-keys",
            "ro.build.type": "userdebug",
            "ro.debuggable": "1",
            "ro.secure": "0",
        }

    monkeypatch.setattr(dd, "get_props", fake_props)

    devices = dd.list_detailed_devices()
    assert devices[0]["is_rooted"] is True
    assert devices[0]["trust"] == "low"
    assert devices[0]["debuggable"] == "1"
    assert devices[0]["secure"] == "0"
