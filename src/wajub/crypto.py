"""Cryptographic helpers for webhook verification."""

import hmac
import hashlib


def hmac_sha256(key: str, data: str) -> str:
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()


def timing_safe_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
