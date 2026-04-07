import asyncio
import time


class RateLimiter:
    """Async rate limiter for NCBI E-utilities (3 req/s without key, 10 with key)."""

    def __init__(self, max_per_second: int = 3):
        self.max_per_second = max_per_second
        self.interval = 1.0 / max_per_second
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            wait = self.interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
