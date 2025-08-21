import importlib
import json
import logging
import sys
from pathlib import Path

# Ensure repository root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.logging_utils.app_logger as al
import utils.logging_utils.log_helpers as lh
import utils.logging_utils.logging_config as lc


def test_logging_helper_writes_to_shared_file():
    importlib.reload(lc)
    importlib.reload(al)
    importlib.reload(lh)

    log_file = Path("logs/app/server.log")
    if log_file.exists():
        log_file.unlink()

    lh.LoggingHelper.info("helper info", logger_name="cli.helper")
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        lh.LoggingHelper.error("helper error", logger_name="cli.helper", exc=exc)

    root = logging.getLogger()
    for h in root.handlers:
        if hasattr(h, "flush"):
            h.flush()

    assert log_file.exists(), "Log file should be created by helper"
    lines = log_file.read_text().strip().splitlines()
    records = [json.loads(line) for line in lines]
    assert any(r["message"] == "helper info" for r in records)
    assert any(r["message"] == "helper error" and "exc_info" in r for r in records)
