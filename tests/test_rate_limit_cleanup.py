from collections import deque

from server import middleware


def setup_function():
    middleware._request_log.clear()
    middleware._last_cleanup = 0


def test_cleanup_removes_empty_and_stale_entries():
    middleware._request_log["empty"] = deque()
    middleware._request_log["stale"] = deque([0])
    now = middleware.RATE_WINDOW_SECS + 1
    middleware._cleanup_request_log(now)
    assert "empty" not in middleware._request_log
    assert "stale" not in middleware._request_log


