"""
Token Bucket Rate Limiter

Thread-safe implementation used to enforce global outbound request limits
for each external service (FIPE API, OLX, WebMotors).

The token bucket algorithm allows bursting up to max_calls then smoothly
queues additional callers until tokens refill.
"""
import asyncio
import threading
import time


class TokenBucketRateLimiter:
    """
    Thread-safe and async-safe token bucket rate limiter.

    Allows up to `max_calls` requests per `period_seconds`, shared globally
    across all instances that hold a reference to the same object.
    """

    def __init__(self, max_calls: int, period_seconds: int):
        self._max_calls = max_calls
        self._period = period_seconds
        self._tokens = float(max_calls)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        refill = elapsed * (self._max_calls / self._period)
        self._tokens = min(self._max_calls, self._tokens + refill)
        self._last_refill = now

    def _try_acquire(self) -> float:
        """Return 0.0 if a token was consumed, else seconds to wait."""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return 0.0
            # Time until next token is available
            return (1.0 - self._tokens) * (self._period / self._max_calls)

    def acquire_sync(self) -> None:
        """Block until a token is available (sync scrapers / threads)."""
        while True:
            wait = self._try_acquire()
            if wait == 0.0:
                return
            time.sleep(wait)

    async def acquire(self) -> None:
        """Async-safe: yield control while waiting for a token."""
        while True:
            wait = self._try_acquire()
            if wait == 0.0:
                return
            await asyncio.sleep(wait)
