"""
Retry handler with exponential backoff and jitter.

Wraps any callable that may fail transiently (HTTP calls to target systems).
On permanent failure (max retries exceeded), the event is moved to the Dead Letter Queue.

Backoff schedule (base=1s, max=30s, jitter=±20%):
  Attempt 1: ~1.0s
  Attempt 2: ~2.0s
  Attempt 3: ~4.0s
  Attempt 4: ~8.0s
  Attempt 5: ~16.0s (capped at 30s)

Jitter prevents thundering herd when multiple events fail simultaneously.
"""

import time
import random
import logging
from typing import Any, Callable
from config import Config

log = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, message: str, last_error: Exception, attempt_count: int):
        super().__init__(message)
        self.last_error    = last_error
        self.attempt_count = attempt_count


def _backoff_delay(attempt: int) -> float:
    """
    Calculate delay for a given attempt number (0-indexed).
    Returns seconds as a float with jitter applied.
    """
    base_delay  = Config.RETRY_BASE_DELAY * (2 ** attempt)
    capped      = min(base_delay, Config.RETRY_MAX_DELAY)
    jitter      = capped * Config.RETRY_JITTER_PCT
    return capped + random.uniform(-jitter, jitter)


def with_retry(fn: Callable, *args, event_id: str = "", **kwargs) -> Any:
    """
    Execute fn(*args, **kwargs) with retry on exception.

    Returns the function's return value on success.
    Raises RetryExhausted after Config.MAX_RETRIES failed attempts.

    Usage:
        result = with_retry(connector.send, payload, event_id="EVT-000001")
    """
    last_exc = None
    for attempt in range(Config.MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            delay = _backoff_delay(attempt)

            if attempt < Config.MAX_RETRIES - 1:
                log.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %.1fs.",
                    attempt + 1, Config.MAX_RETRIES,
                    event_id or "event",
                    str(exc)[:100],
                    delay
                )
                time.sleep(delay)
            else:
                log.error(
                    "All %d attempts exhausted for %s: %s",
                    Config.MAX_RETRIES, event_id or "event", exc
                )

    raise RetryExhausted(
        f"All {Config.MAX_RETRIES} retry attempts exhausted for event {event_id}",
        last_error=last_exc,
        attempt_count=Config.MAX_RETRIES,
    )


def is_retryable(exc: Exception) -> bool:
    """
    Determine if an exception is transient (should be retried) or permanent (should not).

    Transient: network timeouts, HTTP 429, HTTP 5xx
    Permanent: HTTP 400 (bad payload), HTTP 401 (auth), HTTP 404 (not found)
    """
    import requests
    if isinstance(exc, requests.Timeout):
        return True
    if isinstance(exc, requests.ConnectionError):
        return True
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else 0
        return status in (429, 500, 502, 503, 504)
    return True  # default: retry unknown errors
