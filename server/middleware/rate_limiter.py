from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from .settings import Settings


class RateLimiter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.buckets: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=4 * self.settings.rate_limit)
        )
        self._last_cleanup: float = 0.0

    def allow(self, bucket: str, now: float | None = None) -> tuple[bool, int, int]:
        if not bucket:
            raise ValueError("bucket must be non-empty")
        if now is None:
            now = time.monotonic()
        elif now < 0:
            raise ValueError("now must be non-negative")
        window = self.buckets[bucket]
        while window and now - window[0] >= self.settings.rate_window_secs:
            window.popleft()
        if len(window) >= self.settings.rate_limit:
            reset_in = max(0, int(self.settings.rate_window_secs - (now - window[0])))
            remaining = self.settings.rate_limit - len(window)
            return False, remaining, reset_in
        window.append(now)
        remaining = self.settings.rate_limit - len(window)
        reset_in = (
            max(0, int(self.settings.rate_window_secs - (now - window[0])))
            if window
            else self.settings.rate_window_secs
        )
        return True, remaining, reset_in

    def bucket_for(self, presented_key: str | None, ip: str | None) -> str:
        return presented_key or ip or "unknown"

    def cleanup(self, now: float | None = None) -> None:
        if now is None:
            now = time.monotonic()
        if now - self._last_cleanup < self.settings.rate_window_secs:
            return
        self._last_cleanup = now
        stale: list[str] = []
        for bucket, window in list(self.buckets.items()):
            if not window or (now - window[-1] >= self.settings.rate_window_secs):
                stale.append(bucket)
        for bucket in stale:
            self.buckets.pop(bucket, None)
