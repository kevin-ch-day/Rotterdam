import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path for module imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import importlib

import utils.logging_utils.app_logger as al
import utils.logging_utils.logging_config as lc


def test_cli_and_server_write_to_shared_log():
    # Reload logging modules to ensure a clean configuration
    importlib.reload(lc)
    importlib.reload(al)
    app_logger = al.app_logger

    log_file = Path("logs/app/server.log")
    if log_file.exists():
        log_file.unlink()

    # CLI log
    app_logger.get_logger("cli.test").info("cli message")

    # Simulate server log and middleware log using a minimal FastAPI app
    app_logger.get_logger("uvicorn.error").info("server message")

    # Logs from additional modules across the application
    import importlib.machinery as importlib_machinery
    import importlib.util as importlib_util

    from storage import engine_compat

    spec = importlib_util.spec_from_loader(
        "platform.android.analysis.static.ml_model",
        importlib_machinery.SourceFileLoader(
            "platform.android.analysis.static.ml_model",
            str(Path("platform/android/analysis/static/ml_model.py")),
        ),
    )
    ml_model = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(ml_model)
    sys.modules["platform.android.analysis.static.ml_model"] = ml_model

    engine_compat.logger.info("storage message")
    ml_model._LOG.warning("ml model message")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from server.middleware.request_id import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def _root():
        return {"ok": True}

    with TestClient(app) as client:
        client.get("/")

    assert log_file.exists(), "Log file should be created"
    lines = log_file.read_text().strip().splitlines()
    records = [json.loads(line) for line in lines]

    # Ensure messages from CLI, server, middleware, and other modules are present
    assert any(r["module"] == "cli.test" for r in records)
    assert any(r["module"] == "uvicorn.error" for r in records)
    assert any(r["module"] == "rotterdam.request" for r in records)
    assert any(r["module"] == "storage.engine_compat" for r in records)
    assert any(r["module"] == "platform.android.analysis.static.ml_model" for r in records)

    # Verify all *.log files reside within the top-level logs/ directory
    repo_root = Path(__file__).resolve().parents[1]
    unexpected_logs = []
    for path in repo_root.rglob("*.log"):
        rel = path.relative_to(repo_root)
        if rel.parts[0].startswith(".") or rel.parts[0] == "logs":
            continue
        unexpected_logs.append(rel)
    assert not unexpected_logs, f"Log files outside logs dir: {unexpected_logs}"
