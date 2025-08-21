#!/usr/bin/env python3
# File: platform/android/devices/adb.py
"""Shared helpers for invoking ``adb`` commands."""

from __future__ import annotations

from core.tools.adb import adb_path as _adb_path, run as _run_adb

__all__ = ["_run_adb", "_adb_path"]
