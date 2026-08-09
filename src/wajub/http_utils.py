"""HTTP utilities — envelope parsing, API key normalization."""

from __future__ import annotations

import re
import uuid

from wajub.errors import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    WajubError,
)


API_URL = "https://api.wajub.com"


def normalize_api_key(raw: str) -> str:
    key = raw.strip()
    if re.match(r"^bearer\s+", key, re.IGNORECASE):
        key = re.sub(r"^bearer\s+", "", key, flags=re.IGNORECASE).strip()
    return key


def default_api_url() -> str:
    return API_URL


def create_idempotency_key(prefix: str = "wajub") -> str:
    return f"{prefix}-{uuid.uuid4()}"


def pick_resource(body: dict, *keys: str) -> dict:
    for key in keys:
        if key in body and body[key] is not None:
            return dict(body[key]) if isinstance(body[key], dict) else body[key]
    return body


def pick_list(body: dict, *keys: str) -> tuple[list, dict | None]:
    for key in (*keys, "items"):
        if key in body and body[key] is not None:
            meta = body.get("meta")
            return list(body[key]), meta if isinstance(meta, dict) else None
    data = body.get("data", [])
    meta = body.get("meta")
    return list(data) if isinstance(data, list) else [], meta if isinstance(meta, dict) else None


def error_from_response(status: int, body: dict, retry_after: int | None = None) -> WajubError:
    message = body.get("message") if isinstance(body.get("message"), str) else f"Request failed ({status})"
    code = body.get("error_code") or body.get("code") or f"http_{status}"
    if not isinstance(code, str):
        code = f"http_{status}"

    errors = None
    if isinstance(body.get("errors"), dict):
        errors = {}
        for field, value in body["errors"].items():
            errors[str(field)] = str(value[0]) if isinstance(value, list) else str(value)

    common = (str(message), str(code), status, errors, body)

    if status == 401:
        return AuthenticationError(*common)
    if status == 403:
        return PermissionError(*common)
    if status == 404:
        return NotFoundError(*common)
    if status == 429:
        return RateLimitError(*common, retry_after=retry_after)
    if status in (400, 422):
        return InvalidRequestError(*common)

    return WajubError(*common)
