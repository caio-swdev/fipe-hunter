"""
Unit Tests: TokenBucketRateLimiter

Pure logic tests — no network, no DB, no real sleeping.
time.monotonic / time.sleep / asyncio.sleep are patched throughout.
"""
import asyncio
import threading
import time
from unittest.mock import patch

import pytest

from fipe_infra.utils.rate_limiter import TokenBucketRateLimiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_limiter(max_calls: int = 3, period_seconds: int = 60) -> TokenBucketRateLimiter:
    """Create a fresh limiter with a fixed monotonic start time."""
    with patch("time.monotonic", return_value=0.0):
        return TokenBucketRateLimiter(max_calls=max_calls, period_seconds=period_seconds)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_full_bucket_allows_immediate_acquire():
    """Fresh limiter with N tokens — N consecutive acquires return without sleeping."""
    limiter = _make_limiter(max_calls=3)

    sleep_calls = []

    def fake_monotonic():
        return 0.0  # time does not advance → no refill, but bucket starts full

    with patch("time.monotonic", side_effect=fake_monotonic), \
         patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        limiter.acquire_sync()
        limiter.acquire_sync()
        limiter.acquire_sync()

    assert sleep_calls == [], "No sleeping expected when bucket has enough tokens"


def test_depleted_bucket_calls_sleep():
    """After consuming all tokens the next acquire blocks via time.sleep."""
    limiter = _make_limiter(max_calls=2)

    sleep_calls = []
    monotonic_values = iter([
        0.0,   # __init__ _last_refill
        0.0,   # acquire 1 — _refill
        0.0,   # acquire 2 — _refill
        0.0,   # acquire 3 — _refill (bucket empty, compute wait)
        0.0,   # acquire 3 — after sleep, _refill again (simulate time didn't pass)
        60.0,  # acquire 3 — second loop attempt: 60 s later → refill
    ])

    def fake_monotonic():
        return next(monotonic_values)

    with patch("time.monotonic", side_effect=fake_monotonic), \
         patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        limiter.acquire_sync()  # token 1
        limiter.acquire_sync()  # token 2
        limiter.acquire_sync()  # should sleep once

    assert len(sleep_calls) >= 1, "Expected at least one sleep when bucket is empty"
    assert sleep_calls[0] > 0, "Sleep duration must be positive"


def test_token_refill_via_time_advance():
    """Advancing monotonic time causes _refill to restore tokens."""
    limiter = _make_limiter(max_calls=2, period_seconds=60)

    # Drain bucket at t=0
    with patch("time.monotonic", return_value=0.0):
        limiter._refill()
        limiter._tokens = 0.0  # manually drain
        limiter._last_refill = 0.0

    # Advance 60 s → full refill
    with patch("time.monotonic", return_value=60.0):
        limiter._refill()

    assert limiter._tokens == pytest.approx(2.0), "Full refill expected after one period"


@pytest.mark.asyncio
async def test_acquire_async_sleeps_until_token():
    """async acquire() calls asyncio.sleep when bucket is empty."""
    limiter = _make_limiter(max_calls=1)

    sleep_calls = []

    async def fake_sleep(s):
        sleep_calls.append(s)

    monotonic_values = iter([
        0.0,   # _refill inside first _try_acquire (drain)
        0.0,   # _refill inside second _try_acquire (still empty)
        60.0,  # _refill after fake async sleep (60 s later → refill)
    ])

    def fake_monotonic():
        return next(monotonic_values)

    # Drain the one token first
    limiter._tokens = 0.0
    limiter._last_refill = 0.0

    with patch("time.monotonic", side_effect=fake_monotonic), \
         patch("asyncio.sleep", side_effect=fake_sleep):
        await limiter.acquire()

    assert len(sleep_calls) >= 1, "asyncio.sleep should be called when bucket is empty"
    assert sleep_calls[0] > 0


def test_acquire_sync_thread_safety():
    """5 threads competing on a 2-token limiter — no race conditions, no errors."""
    results = []
    errors = []

    limiter = _make_limiter(max_calls=2, period_seconds=1)

    def worker():
        try:
            # Let each thread drain in real time (tiny limiter, fast refill)
            limiter.acquire_sync()
            results.append(1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert errors == [], f"Thread safety errors: {errors}"
    assert len(results) == 5, "All 5 threads should have acquired a token eventually"
