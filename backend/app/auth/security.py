from __future__ import annotations

import hashlib
import hmac
import secrets

from app.config import get_settings

KEY_PREFIX = "sk_live_"
VISIBLE_PREFIX_LENGTH = 18


def generate_api_key() -> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"


def get_key_prefix(raw_key: str) -> str:
    return raw_key[:VISIBLE_PREFIX_LENGTH]


def hash_api_key(raw_key: str) -> str:
    settings = get_settings()
    return hmac.new(
        settings.api_key_pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_api_key(raw_key: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), expected_hash)
