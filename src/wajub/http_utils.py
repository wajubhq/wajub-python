"""HTTP utilities — envelope parsing, API key normalization."""

from __future__ import annotations

import re
import uuid
from dataclasses import replace
from typing import Any
from urllib.parse import unquote

from wajub.errors import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    WajubError,
)
from wajub.request_options import RequestOptions

API_URL = "https://api.wajub.com"


def normalize_api_key(raw: str) -> str:
    key = raw.strip()
    if re.match(r"^bearer\s+", key, re.IGNORECASE):
        key = re.sub(r"^bearer\s+", "", key, flags=re.IGNORECASE).strip()
    return key


def default_api_url() -> str:
    return API_URL


def path_id(value: object, name: str = "id") -> str:
    """An id to put in a request path, refused if it could reach another route.

    The API decodes ``%2F`` before matching routes, so ``pay_1/refunds`` and
    ``pay_1%2Frefunds`` would both reach ``/payments/{id}/refunds``. Wajub ids
    never contain a slash, and are never empty, ``.`` or ``..``.
    """
    text = str(value)
    decoded = unquote(text)
    if "/" in decoded or decoded.strip() in ("", ".", ".."):
        raise ValueError(
            f"Wajub: {name} {text!r} is not a Wajub id; "
            "an id is never empty and never contains '/'"
        )
    return text


def create_idempotency_key(prefix: str = "wajub") -> str:
    return f"{prefix}-{uuid.uuid4()}"


_IDEMPOTENCY_KEY_PARAMS = ("idempotencyKey", "idempotency_key")


def is_idempotency_key_header(name: str) -> bool:
    return name.lower() == "idempotency-key"


def request_options_idempotency_key(options: RequestOptions | None) -> str | None:
    """The idempotency key set in the request options, if any.

    It can be given as ``idempotency_key`` or as an Idempotency-Key header, in
    any case; given more than once, it must be the same key. An empty key
    counts as none, as in the params.
    """
    if options is None:
        return None
    given: dict[str, Any] = {}
    if options.idempotency_key not in (None, ""):
        given["RequestOptions(idempotency_key=...)"] = options.idempotency_key
    for name, value in (options.headers or {}).items():
        if is_idempotency_key_header(name) and value not in (None, ""):
            given[f"the {name!r} header"] = value
    for where, key in given.items():
        if not isinstance(key, str):
            raise TypeError(
                f"Wajub: the idempotency key in {where} must be a string, "
                f"not {type(key).__name__}"
            )
    if len(set(given.values())) > 1:
        raise ValueError(
            "Wajub: RequestOptions carries two different idempotency keys "
            f"({' and '.join(given)}); pass it once, as RequestOptions(idempotency_key=...)"
        )
    return next(iter(given.values()), None)


def idempotency_key_from_params(
    params: dict[str, Any] | None, options: RequestOptions | None
) -> tuple[dict[str, Any] | None, RequestOptions | None]:
    """Move an idempotency key given in the params to the request options.

    Returns the body to send and the options to send it with. The key is sent
    as the Idempotency-Key header, never in the body, and the caller's dict is
    left as it was so that the same params can be sent again.
    """
    if params is None:
        return None, options
    body = dict(params)
    keys = {name: body.pop(name) for name in _IDEMPOTENCY_KEY_PARAMS if name in body}
    given = {name: key for name, key in keys.items() if key is not None and key != ""}
    for name, key in given.items():
        if not isinstance(key, str):
            raise TypeError(
                f"Wajub: the idempotency key in params[{name!r}] must be a string, "
                f"not {type(key).__name__}"
            )
    if len(set(given.values())) > 1:
        raise ValueError(
            "Wajub: params has two different idempotency keys "
            "('idempotencyKey' and 'idempotency_key'); pass one"
        )
    if not given:
        return body, options

    key = next(iter(given.values()))
    if options is None:
        return body, RequestOptions(idempotency_key=key)
    existing = request_options_idempotency_key(options)
    if existing is not None and existing != key:
        raise ValueError(
            "Wajub: params and RequestOptions carry two different idempotency keys; "
            "pass it once, as RequestOptions(idempotency_key=...)"
        )
    return body, replace(options, idempotency_key=key)


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
    message = body.get("message")
    if not isinstance(message, str):
        message = f"Request failed ({status})"
    code = body.get("error_code") or body.get("code") or f"http_{status}"
    if not isinstance(code, str):
        code = f"http_{status}"

    errors = None
    field_errors = None
    if isinstance(body.get("errors"), dict):
        errors = {}
        field_errors = {}
        for field, value in body["errors"].items():
            messages = [str(item) for item in value] if isinstance(value, list) else [str(value)]
            if messages:
                errors[str(field)] = messages[0]
                field_errors[str(field)] = messages

    common = (str(message), str(code), status, errors, body)
    extra = {"field_errors": field_errors}

    if status == 401:
        return AuthenticationError(*common, **extra)
    if status == 403:
        return PermissionError(*common, **extra)
    if status == 404:
        return NotFoundError(*common, **extra)
    if status == 429:
        return RateLimitError(*common, retry_after=retry_after, **extra)
    if status in (400, 422):
        return InvalidRequestError(*common, **extra)

    return WajubError(*common, **extra)
