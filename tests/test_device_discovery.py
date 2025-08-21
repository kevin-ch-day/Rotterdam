from rotterdam.android.devices import discovery


def test_list_detailed_devices_stub(monkeypatch):
    """Stub ADB interaction and ensure device info is parsed."""
    sample_output = "emulator-5554 device product:sdk_gphone_x86 transport_id:1"

    def fake_check() -> str:
        return sample_output

    def fake_get_props(serial: str):
        return {
            "ro.product.manufacturer": "Google",
            "ro.product.model": "sdk_gphone_x86",
            "ro.build.version.release": "11",
            "ro.build.version.sdk": "30",
            "ro.product.cpu.abi": "x86",
            "ro.board.platform": "generic_x86",
            "ro.hardware": "ranchu",
            "ro.build.tags": "test-keys",
            "ro.build.type": "userdebug",
            "ro.debuggable": "1",
            "ro.secure": "0",
            "ro.build.fingerprint": "fp",
        }

    monkeypatch.setattr(discovery, "check_connected_devices", fake_check)
    monkeypatch.setattr(discovery, "get_props", fake_get_props)
    monkeypatch.setattr(discovery, "_infer_is_emulator", lambda s, p, m: True)
    monkeypatch.setattr(discovery, "_infer_connection_kind", lambda s, m: "usb")
    monkeypatch.setattr(discovery, "_infer_root_status", lambda p: False)
    monkeypatch.setattr(discovery, "_short_fingerprint", lambda fp: "shortfp")

    devices = discovery.list_detailed_devices()
    assert devices and devices[0]["serial"] == "emulator-5554"
    assert devices[0]["manufacturer"] == "Google"
    assert devices[0]["type"] == "emulator"
