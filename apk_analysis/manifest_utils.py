"""Helpers for parsing AndroidManifest.xml files."""

from __future__ import annotations

from typing import Any, Dict, List

from app_utils.error_utils import safe_fromstring


def extract_permission_details(manifest_text: str) -> List[Dict[str, Any]]:
    """Return structured information for each ``uses-permission`` tag.

    Each entry contains the permission ``name``, the originating ``tag``
    (``uses-permission`` or ``uses-permission-sdk-23``), and any integer
    ``max_sdk_version`` constraint.
    """

    ns = {"android": "http://schemas.android.com/apk/res/android"}
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return []
    details: List[Dict[str, Any]] = []
    for tag in ["uses-permission", "uses-permission-sdk-23"]:
        for elem in root.findall(tag):
            name = elem.get(f"{{{ns['android']}}}name") or ""
            max_sdk = elem.get(f"{{{ns['android']}}}maxSdkVersion")
            details.append(
                {
                    "name": name,
                    "tag": tag,
                    "max_sdk_version": int(max_sdk) if max_sdk and max_sdk.isdigit() else None,
                }
            )
    return details


def extract_permissions(manifest_text: str) -> List[str]:
    """Return unique permission strings from an AndroidManifest.xml text."""
    return sorted({d["name"] for d in extract_permission_details(manifest_text) if d["name"]})


def extract_components(manifest_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse an AndroidManifest.xml and return exported components.

    The return value maps component tag names (activity, service, receiver,
    provider) to a list of dictionaries describing each component. Each
    dictionary contains the component ``name``, whether it is ``exported``, and
    any associated ``permission``.
    """
    ns = {"android": "http://schemas.android.com/apk/res/android"}
    result: Dict[str, List[Dict[str, Any]]] = {tag: [] for tag in ["activity", "service", "receiver", "provider"]}
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return result

    app = root.find("application")
    if app is None:
        return result

    for tag in result.keys():
        for elem in app.findall(tag):
            name = elem.get(f"{{{ns['android']}}}name") or ""
            exported = elem.get(f"{{{ns['android']}}}exported")
            permission = elem.get(f"{{{ns['android']}}}permission") or ""
            result[tag].append(
                {
                    "name": name,
                    "exported": (exported == "true") if exported is not None else False,
                    "permission": permission,
                }
            )
    return result


def extract_sdk_info(manifest_text: str) -> Dict[str, int]:
    """Return SDK version information from the manifest."""
    ns = {"android": "http://schemas.android.com/apk/res/android"}
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return {}
    info: Dict[str, int] = {}
    sdk = root.find("uses-sdk")
    if sdk is None:
        return info
    for attr in ["minSdkVersion", "targetSdkVersion", "maxSdkVersion"]:
        val = sdk.get(f"{{{ns['android']}}}{attr}")
        if val and val.isdigit():
            info[attr] = int(val)
    return info


def extract_features(manifest_text: str) -> List[Dict[str, Any]]:
    """Return a list of features requested by the app."""
    ns = {"android": "http://schemas.android.com/apk/res/android"}
    features: List[Dict[str, Any]] = []
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return features
    for feat in root.findall("uses-feature"):
        name = feat.get(f"{{{ns['android']}}}name") or ""
        required = feat.get(f"{{{ns['android']}}}required")
        features.append({"name": name, "required": required != "false"})
    return features


def extract_app_flags(manifest_text: str) -> Dict[str, bool]:
    """Return notable boolean flags from the <application> tag."""
    ns = {"android": "http://schemas.android.com/apk/res/android"}
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return {}
    app = root.find("application")
    if app is None:
        return {}
    result: Dict[str, bool] = {}
    for attr in ["debuggable", "allowBackup", "usesCleartextTraffic"]:
        val = app.get(f"{{{ns['android']}}}{attr}")
        if val is not None:
            result[attr] = val == "true"
    return result


def extract_metadata(manifest_text: str) -> List[Dict[str, str]]:
    """Return ``meta-data`` entries from the ``application`` tag."""
    ns = {"android": "http://schemas.android.com/apk/res/android"}
    root = safe_fromstring(manifest_text, description="manifest")
    if root is None:
        return []
    app = root.find("application")
    if app is None:
        return []
    data: List[Dict[str, str]] = []
    for item in app.findall("meta-data"):
        name = item.get(f"{{{ns['android']}}}name") or ""
        value = item.get(f"{{{ns['android']}}}value") or ""
        data.append({"name": name, "value": value})
    return data
