"""Retry policy for transient API failures."""

from __future__ import annotations

import email.utils
import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

MAX_RETRIES = 2
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def should_retry_status(status: int) -> bool:
    return status in RETRYABLE_STATUS


def delay_seconds(attempt: int, response: httpx.Response | None = None) -> float:
    if response is not None:
        retry_after = parse_retry_after(response)
        if retry_after is not None:
            return float(retry_after)

    base = 0.5 * (2 ** (attempt - 1))
    jitter = 0.5 + random.random() * 0.5
    return base * jitter


def parse_retry_after(response: httpx.Response) -> int | None:
    header = response.headers.get("Retry-After", "").strip()
    if not header:
        return None

    if header.isdigit():
        return int(header)

    try:
        parsed = email.utils.parsedate_to_datetime(header)
        if parsed is not None:
            return max(0, int(parsed.timestamp() - time.time()))
    except (TypeError, ValueError, OverflowError):
        pass

    return None
