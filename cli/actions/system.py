from __future__ import annotations

import shutil

from core.diagnostics import BinaryCheck, ModuleCheck, SystemDoctor
from devices import adb
from utils.display_utils import display


def run_doctor() -> None:
    """Check availability of required binaries and Python modules."""
    checks = [
        *(BinaryCheck(b) for b in ["adb", "aapt2", "apktool", "jadx", "yara", "java"]),
        *(
            ModuleCheck(m)
            for m in [
                "androguard",
                "fastapi",
                "uvicorn",
                "sqlalchemy",
                "mysql.connector",
            ]
        ),
    ]

    doctor = SystemDoctor(checks)
    results = doctor.run()

    display.print_section("Binary Dependencies")
    for res in (r for r in results if r.category == "binary"):
        if res.ok:
            display.ok(f"{res.name} : {res.detail}")
        else:
            display.fail(f"{res.name} : {res.detail}")

    display.print_section("Python Modules")
    for res in (r for r in results if r.category == "module"):
        if res.ok:
            display.ok(f"{res.name} : {res.detail}")
        else:
            display.fail(f"{res.name} : {res.detail}")

    if doctor.has_issues:
        display.warn("One or more diagnostics failed. Review the flags above.")


def run_health_check() -> None:
    """Run basic health checks for required tools and services."""

    display.print_section("System Health Check")

    # -------------------------
    # ADB
    # -------------------------
    try:
        proc = adb._run_adb(["version"])
        version = (proc.stdout or "").strip().splitlines()[0]
        display.ok(f"adb: {version}")

        try:
            dev_proc = adb._run_adb(["devices"])
            lines = [ln for ln in (dev_proc.stdout or "").splitlines()[1:] if ln.strip()]
            if not lines:
                display.warn(
                    "No devices detected. On Fedora ensure 'android-udev-rules' is installed and USB debugging is enabled."
                )
            elif any("unauthorized" in ln for ln in lines):
                display.warn(
                    "Device connected but unauthorized. On Fedora accept the RSA prompt and run 'adb kill-server && adb devices'."
                )
        except Exception:
            pass
    except Exception as exc:
        display.fail(f"adb check failed: {exc}")
        display.note(
            "Install with 'sudo dnf install android-tools'. If a device is attached but not detected, install 'android-udev-rules' and enable USB debugging."
        )

    # -------------------------
    # androguard
    # -------------------------
    try:
        import androguard  # type: ignore  # noqa: F401

        display.ok("androguard: import OK")
    except Exception:
        display.fail("androguard: not importable")
        display.note("Install via 'pip install androguard' or 'sudo dnf install androguard'.")

    # -------------------------
    # apktool
    # -------------------------
    if shutil.which("apktool"):
        display.ok("apktool: found")
    else:
        display.fail("apktool: not found in PATH")
        display.note("Install with 'sudo dnf install apktool'.")

    # -------------------------
    # Database
    # -------------------------
    try:
        from mysql.connector import Error

        from database import DatabaseCore, DbEngine
    except Exception as exc:  # pragma: no cover - environment specific
        display.fail(f"database libraries missing: {exc}")
        display.note(
            "Install MySQL connector via 'pip install mysql-connector-python' or 'sudo dnf install python3-mysql-connector'."
        )
        return

    try:
        with DatabaseCore.from_config() as core:
            engine = DbEngine(core)
            if engine.is_ready():
                display.ok("database: connection ready")
            else:
                display.fail("database: unable to connect")
                display.note(
                    "Check database configuration and ensure the service is running. On Fedora start with 'sudo systemctl start mariadb'."
                )
    except Error as exc:  # pragma: no cover - environment specific
        display.fail(f"database error: {exc}")
        display.note(
            "Ensure credentials are correct and the database server is running. On Fedora install it with 'sudo dnf install mariadb-server'."
        )
