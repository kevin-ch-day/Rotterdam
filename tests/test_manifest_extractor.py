import pytest
from rotterdam.android.analysis.static.extractors.manifest import extract_permissions


@pytest.fixture
def minimal_manifest() -> str:
    return (
        "<manifest xmlns:android='http://schemas.android.com/apk/res/android'>"
        "<uses-permission android:name='android.permission.INTERNET'/>"
        "<application/>"
        "</manifest>"
    )


def test_extract_permissions(minimal_manifest):
    perms = extract_permissions(minimal_manifest)
    assert perms == ["android.permission.INTERNET"]
