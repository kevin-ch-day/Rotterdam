from __future__ import annotations

from utils.display_utils import display
from core.diagnostics import BinaryCheck, ModuleCheck, SystemDoctor


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

