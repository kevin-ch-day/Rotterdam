"""Helpers for analyzing Android permissions."""

from __future__ import annotations

from typing import Any, Dict, List

# A subset of dangerous permissions as defined by Android
# https://developer.android.com/guide/topics/permissions/overview#dangerous_permissions
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_CALENDAR",
    "android.permission.WRITE_CALENDAR",
    "android.permission.CAMERA",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.GET_ACCOUNTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_PHONE_STATE",
    "android.permission.CALL_PHONE",
    "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG",
    "com.android.voicemail.permission.ADD_VOICEMAIL",
    "android.permission.USE_SIP",
    "android.permission.PROCESS_OUTGOING_CALLS",
    "android.permission.BODY_SENSORS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_WAP_PUSH",
    "android.permission.RECEIVE_MMS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
}


def categorize_permissions(perms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return metadata for each permission including whether it's dangerous."""
    details: List[Dict[str, Any]] = []
    for perm in perms:
        entry = perm.copy()
        entry["dangerous"] = entry.get("name") in DANGEROUS_PERMISSIONS
        details.append(entry)
    return details
