"""
Global outbound rate limiter singletons.

Imported by clients/scrapers to enforce per-service outbound limits:
  - FIPE API:    200 calls/hour
  - OLX:        100 calls/hour
  - WebMotors:   60 calls/hour

These are module-level singletons so state is shared across all requests
within the same process.
"""
from fipe_infra.utils.rate_limiter import TokenBucketRateLimiter

fipe_limiter = TokenBucketRateLimiter(max_calls=200, period_seconds=3600)
olx_limiter = TokenBucketRateLimiter(max_calls=100, period_seconds=3600)
webmotors_limiter = TokenBucketRateLimiter(max_calls=60, period_seconds=3600)
