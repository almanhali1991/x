"""
Core security utilities for XMOS.

Handles password hashing, token generation, and secret management.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Any

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import settings


def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure random secret key."""
    return secrets.token_hex(length)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Hash a password using SHA-256 with salt.

    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    salted_password = f"{salt}{password}".encode("utf-8")
    hashed = hashlib.sha256(salted_password).hexdigest()

    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against its hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, hashed_password)


class TokenManager:
    """Manage secure tokens for OAuth and sessions."""

    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or settings.secret_key
        self.serializer = URLSafeTimedSerializer(self.secret_key)

    def generate_token(self, data: dict[str, Any], expires_in_hours: int = 24) -> str:
        """Generate a signed token with expiration."""
        payload = {
            "data": data,
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        }
        return self.serializer.dumps(payload)

    def verify_token(self, token: str, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Verify and decode a token.

        Returns:
            Decoded data or None if invalid/expired.
        """
        try:
            max_age_seconds = max_age_hours * 3600
            payload = self.serializer.loads(token, max_age=max_age_seconds)
            return payload.get("data")
        except (BadSignature, SignatureExpired):
            return None

    def generate_state_token(self) -> str:
        """Generate a state token for OAuth CSRF protection."""
        return secrets.token_urlsafe(32)


# Default token manager instance
token_manager = TokenManager()


def redact_secret(value: str, visible_chars: int = 4) -> str:
    """Redact a secret value for logging."""
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars * 2)}{value[-visible_chars:]}"


def redact_dict(data: dict[str, Any], sensitive_keys: list[str] | None = None) -> dict[str, Any]:
    """
    Redact sensitive values in a dictionary.

    Args:
        data: Dictionary to redact
        sensitive_keys: List of keys to redact (case-insensitive matching)

    Returns:
        Redacted dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "client_secret",
        ]

    result = {}
    for key, value in data.items():
        if any(sensitive.lower() in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str):
                result[key] = redact_secret(value)
            else:
                result[key] = "[REDACTED]"
        else:
            result[key] = value

    return result
