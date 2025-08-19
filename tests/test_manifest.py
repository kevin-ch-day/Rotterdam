from analysis.manifest import (
    extract_permission_details,
    extract_permissions,
    extract_components,
    extract_sdk_info,
    extract_features,
    extract_app_flags,
    extract_metadata,
)

MANIFEST = """<?xml version='1.0'?>
<manifest xmlns:android='http://schemas.android.com/apk/res/android'>
    <uses-permission android:name='android.permission.INTERNET'/>
    <uses-permission-sdk-23 android:name='android.permission.CAMERA' android:maxSdkVersion='28'/>
    <uses-sdk android:minSdkVersion='21' android:targetSdkVersion='33'/>
    <uses-feature android:name='feature1' android:required='true'/>
    <uses-feature android:name='feature2' android:required='false'/>
    <application android:debuggable='true' android:allowBackup='false' android:usesCleartextTraffic='true'>
        <activity android:name='.MainActivity' android:exported='true' android:permission='perm'/>
        <service android:name='.MyService'/>
        <receiver android:name='.MyReceiver' android:exported='false'/>
        <provider android:name='.MyProvider' android:exported='true' android:permission='provider_perm'/>
        <meta-data android:name='key' android:value='val'/>
    </application>
</manifest>
"""


def test_extract_permission_details():
    details = extract_permission_details(MANIFEST)
    assert {
        "name": "android.permission.INTERNET",
        "tag": "uses-permission",
        "max_sdk_version": None,
    } in details
    assert {
        "name": "android.permission.CAMERA",
        "tag": "uses-permission-sdk-23",
        "max_sdk_version": 28,
    } in details


def test_extract_permissions():
    perms = extract_permissions(MANIFEST)
    assert perms == ["android.permission.CAMERA", "android.permission.INTERNET"]


def test_extract_components():
    comps = extract_components(MANIFEST)
    assert comps["activity"][0] == {
        "name": ".MainActivity",
        "exported": True,
        "permission": "perm",
    }
    assert comps["service"][0] == {
        "name": ".MyService",
        "exported": False,
        "permission": "",
    }
    assert comps["receiver"][0] == {
        "name": ".MyReceiver",
        "exported": False,
        "permission": "",
    }
    assert comps["provider"][0] == {
        "name": ".MyProvider",
        "exported": True,
        "permission": "provider_perm",
    }


def test_extract_sdk_info():
    info = extract_sdk_info(MANIFEST)
    assert info == {"minSdkVersion": 21, "targetSdkVersion": 33}


def test_extract_features():
    features = extract_features(MANIFEST)
    assert features == [
        {"name": "feature1", "required": True},
        {"name": "feature2", "required": False},
    ]


def test_extract_app_flags():
    flags = extract_app_flags(MANIFEST)
    assert flags == {
        "debuggable": True,
        "allowBackup": False,
        "usesCleartextTraffic": True,
    }


def test_extract_metadata():
    metadata = extract_metadata(MANIFEST)
    assert metadata == [{"name": "key", "value": "val"}]
