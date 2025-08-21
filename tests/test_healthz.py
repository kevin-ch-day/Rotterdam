import sys
import types

from fastapi.testclient import TestClient

# Stub devices package to avoid platform import issues.
fake_devices = types.ModuleType("devices")
fake_service = types.ModuleType("devices.service")
fake_service.discover = lambda: []
fake_service.list_packages = lambda *_: []
fake_service.props = lambda *_: None
sys.modules.setdefault("devices", fake_devices)
sys.modules.setdefault("devices.service", fake_service)

# Stub reporting module used by job_service.
fake_reporting = types.ModuleType("reporting")
fake_reporting.generate = lambda *_, **__: {}
sys.modules.setdefault("reporting", fake_reporting)

from server.main import app


def test_healthz_endpoint():
    """Ensure the liveness endpoint responds."""
    with TestClient(app) as client:
        resp = client.get("/_healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
