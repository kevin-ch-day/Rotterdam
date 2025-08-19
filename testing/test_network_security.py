from analysis import parse_network_security_config


def test_parse_network_security_config():
    xml = (
        '<network-security-config xmlns:android="http://schemas.android.com/apk/res/android">'
        '<base-config android:cleartextTrafficPermitted="true" />'
        '<domain-config>'
        '<domain includeSubdomains="true">example.com</domain>'
        '<pin-set>'
        '<pin digest="SHA-256">AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</pin>'
        '</pin-set>'
        '</domain-config>'
        '<debug-overrides />'
        '</network-security-config>'
    )
    info = parse_network_security_config(xml)
    assert info["cleartext_permitted"] is True
    assert info["certificate_pinning"] is True
    assert info["debug_overrides"] is True
