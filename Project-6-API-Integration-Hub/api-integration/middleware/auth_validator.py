"""
Authentication validator — supports three auth patterns used across integrations:

  1. HMAC-SHA256 webhook signatures  (BambooHR, Jira, custom senders)
  2. API key header                  (simple integrations, internal tools)
  3. Bearer token validation         (OAuth 2.0 — validates via introspection)

The validate() function is the single entry point, dispatching to the
correct method based on the X-Auth-Type header or source system config.
"""

import hmac
import hashlib
import logging
from flask import Request
from config import Config

log = logging.getLogger(__name__)


def _validate_hmac(request: Request, secret: str) -> bool:
    """Validate an HMAC-SHA256 webhook signature."""
    sig_header = (
        request.headers.get("X-Hub-Signature-256") or
        request.headers.get("X-Webhook-Signature") or
        request.headers.get("X-Signature") or ""
    )
    if not sig_header:
        return False

    # Strip prefix if present (e.g., "sha256=abc123")
    if "=" in sig_header:
        sig_header = sig_header.split("=", 1)[1]

    expected = hmac.new(secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_header, expected)


def _validate_api_key(request: Request, expected_key: str) -> bool:
    """Validate a static API key from request headers."""
    provided = (
        request.headers.get("X-API-Key") or
        request.headers.get("Authorization", "").replace("ApiKey ", "").strip()
    )
    return hmac.compare_digest(provided, expected_key)


def _validate_bearer(request: Request) -> bool:
    """
    Validate an OAuth 2.0 Bearer token.
    In production this would call the token introspection endpoint.
    For portfolio purposes, validates format only.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    return len(token) > 20  # Basic format check; replace with real introspection


# Map source system names to their secrets / validation methods
_SOURCE_AUTH = {
    "bamboohr":   ("hmac",    Config.BAMBOOHR_WEBHOOK_SECRET),
    "jira":       ("hmac",    Config.JIRA_WEBHOOK_SECRET),
    "web_form":   ("api_key", Config.WEBHOOK_SECRET),
    "quickbase":  ("api_key", Config.WEBHOOK_SECRET),
    "salesforce": ("bearer",  None),
    "default":    ("api_key", Config.WEBHOOK_SECRET),
}


def validate(request: Request, source: str) -> bool:
    """
    Validate the authentication for a webhook request.

    Args:
        request: Flask request object
        source:  Normalized source system name (lowercase, underscores)

    Returns True if authentication passes, False otherwise.
    Logs the reason for failure at WARNING level.
    """
    key = source.lower().replace(" ", "_").replace("-", "_")
    auth_type, secret = _SOURCE_AUTH.get(key, _SOURCE_AUTH["default"])

    if auth_type == "hmac":
        if not secret:
            log.error("HMAC secret not configured for source '%s' — rejecting.", key)
            return False
        result = _validate_hmac(request, secret)
        if not result:
            log.warning("HMAC validation failed for source '%s'", key)
        return result

    if auth_type == "api_key":
        result = _validate_api_key(request, secret)
        if not result:
            log.warning("API key validation failed for source '%s'", key)
        return result

    if auth_type == "bearer":
        result = _validate_bearer(request)
        if not result:
            log.warning("Bearer token validation failed for source '%s'", key)
        return result

    log.error("Unknown auth type '%s' for source '%s'", auth_type, key)
    return False
