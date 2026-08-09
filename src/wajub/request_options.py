"""Request options for mutating API calls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestOptions:
    idempotency_key: str | None = None
    headers: dict[str, str] | None = None
    sync: str | None = None
