"""
Shared utility functions.

Minimal set of truly reusable utilities. Module-specific utilities
should remain in their respective modules.
"""
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any


def generate_id() -> uuid.UUID:
    """Generate a new UUID4."""
    return uuid.uuid4()


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return secrets.token_urlsafe(16)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_dict(data: dict[str, Any], sensitive_keys: set[str]) -> dict[str, Any]:
    """
    Sanitize dictionary by redacting sensitive keys.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: Set of keys to redact
        
    Returns:
        Sanitized dictionary with sensitive values redacted
    """
    result = {}
    for key, value in data.items():
        if key.lower() in {k.lower() for k in sensitive_keys}:
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, sensitive_keys)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# Common sensitive keys to redact
SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "private_key",
    "access_token",
    "refresh_token",
}
