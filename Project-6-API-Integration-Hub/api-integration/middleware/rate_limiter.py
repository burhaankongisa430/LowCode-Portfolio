"""
Token bucket rate limiter — per source system.

Algorithm: Each source system has a bucket with a maximum capacity
equal to its per-minute rate limit. Tokens are replenished continuously
at (limit / 60) tokens per second. Each request consumes one token.
If the bucket is empty, the request is rejected with HTTP 429.

This is in-memory and single-instance. See README trade-offs for
upgrade path to Redis for multi-instance deployments.
"""

import threading
import time
from config import Config


class TokenBucket:
    """Thread-safe token bucket for a single source system."""

    def __init__(self, rate_per_minute: int):
        self._capacity    = rate_per_minute
        self._tokens      = float(rate_per_minute)
        self._rate        = rate_per_minute / 60.0  # tokens per second
        self._last_refill = time.monotonic()
        self._lock        = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def consume(self) -> bool:
        """Return True if a token was consumed (request allowed). False = rate limited."""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    @property
    def available(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


class RateLimiter:
    """Global rate limiter — one TokenBucket per source system."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, source: str) -> TokenBucket:
        key = source.lower().replace(" ", "_").replace("-", "_")
        with self._lock:
            if key not in self._buckets:
                limit = Config.RATE_LIMITS.get(key, Config.RATE_LIMITS["default"])
                self._buckets[key] = TokenBucket(limit)
        return self._buckets[key]

    def check(self, source: str) -> bool:
        """Return True if the request is allowed, False if rate limited."""
        return self._get_bucket(source).consume()

    def available_tokens(self, source: str) -> float:
        return self._get_bucket(source).available

    def status(self) -> dict:
        """Return token counts for all known buckets (useful for monitoring)."""
        return {
            src: round(bucket.available, 1)
            for src, bucket in self._buckets.items()
        }


# Singleton — shared across all requests in the process
rate_limiter = RateLimiter()
