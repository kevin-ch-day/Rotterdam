import inspect

from sandbox import permission_monitor
from sandbox.permission_monitor import PermissionMonitor


def test_permission_monitor_summary(monkeypatch):
    sample_output = (
        "Op ACCESS_FINE_LOCATION from uid 1000 pkg com.example\n"
        "Op READ_SMS from uid 1001 pkg com.sms.app"
    )
    monkeypatch.setattr(permission_monitor, "_run_shell", lambda cmd: sample_output)
    monitor = PermissionMonitor()
    monitor.poll()
    assert monitor.get_summary() == {
        "ACCESS_FINE_LOCATION": 1,
        "READ_SMS": 1,
    }
    logs = list(monitor.get_logs())
    assert len(logs) == 2
    assert logs[0].permission == "ACCESS_FINE_LOCATION"
    assert logs[0].component == "com.example"
    monitor.clear()
    assert monitor.get_summary() == {}
    assert list(monitor.get_logs()) == []


def test_single_collect_permissions_definition():
    src = inspect.getsource(permission_monitor)
    assert src.count("def collect_permissions") == 1
