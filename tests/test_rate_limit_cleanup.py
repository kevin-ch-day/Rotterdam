from collections import deque

from server.middleware.rate_limiter import RateLimiter
from server.middleware.settings import Settings


def test_cleanup_removes_empty_and_stale_entries():
    settings = Settings.from_env()
    limiter = RateLimiter(settings)
    limiter.buckets["empty"] = deque()
    limiter.buckets["stale"] = deque([0])
    now = settings.rate_window_secs + 1
    limiter.cleanup(now)
    assert "empty" not in limiter.buckets
    assert "stale" not in limiter.buckets
