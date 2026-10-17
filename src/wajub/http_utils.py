"""HTTP utilities — envelope parsing, API key normalization."""

from __future__ import annotations

import re
import uuid
from dataclasses import replace
from typing import Any
from urllib.parse import quote, unquote

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
    # "Bearer" alone, once stripped, is a prefix without a key.
    if re.match(r"^bearer(\s+|$)", key, re.IGNORECASE):
        key = re.sub(r"^bearer(\s+|$)", "", key, flags=re.IGNORECASE).strip()
    return key


# Wajub keys are printable ASCII without spaces: anything else cannot be sent
# in a header, and the HTTP client's error would quote the key.
_SENDABLE_API_KEY = re.compile(r"[\x21-\x7e]+")


def api_key_header(raw: object, where: str = "the API key") -> str:
    """The API key as sent in the Authorization header, refused if unsendable.

    ``where`` names the key in the errors, which never contain the key.
    """
    if isinstance(raw, bytes):
        # Decoded outside the except block, so that no error carries the key.
        text = raw.decode("ascii") if raw.isascii() else None
        if text is None:
            raise ValueError(_unsendable_api_key(where))
        raw = text
    if not isinstance(raw, str):
        raise TypeError(f"Wajub: {where} must be a string, not {type(raw).__name__}")
    key = normalize_api_key(raw)
    if not key:
        raise ValueError(f"Wajub: {where} is empty")
    if not _SENDABLE_API_KEY.fullmatch(key):
        raise ValueError(_unsendable_api_key(where))
    return key


def _unsendable_api_key(where: str) -> str:
    return (
        f"Wajub: {where} contains a character that cannot be sent: a space, a line "
        "break or a non-ASCII character. Copy it again from the dashboard."
    )


# Control characters, line breaks included, cannot be sent in a header value.
_UNSENDABLE_HEADER_CHAR = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")


def header_value(name: str, value: Any) -> Any:
    """A header value as sent, without the spaces around it.

    A value with a line break, a control character or, in a string, a
    non-ASCII character is refused before anything is sent. The error names the
    header, never the value. Bytes are sent as given, as before.
    """
    if isinstance(value, bytes):
        text = value.decode("latin-1")
    elif isinstance(value, str):
        text = value
    else:
        return value
    text = text.strip(" \t")
    if (isinstance(value, str) and not text.isascii()) or _UNSENDABLE_HEADER_CHAR.search(text):
        raise ValueError(
            f"Wajub: the {name!r} header contains a character that cannot be sent: "
            "a line break, a control character or a non-ASCII character"
        )
    return text if isinstance(value, str) else text.encode("latin-1")


def default_api_url() -> str:
    return API_URL


def path_id(value: object, name: str = "id") -> str:
    """An id to put in a request path, refused if it could reach another route.

    The API decodes ``%2F`` before matching routes, so ``pay_1/refunds`` and
    ``pay_1%2Frefunds`` would both reach ``/payments/{id}/refunds``. Wajub ids
    are strings, or UUIDs for some resources, that never contain a slash, and
    are never empty, ``.`` or ``..``. The id is then escaped, so that ``?``,
    ``#`` or ``%`` stay in it.
    """
    if isinstance(value, uuid.UUID):
        value = str(value)
    if not isinstance(value, str):
        raise TypeError(f"Wajub: {name} must be a string or a UUID, not {type(value).__name__}")
    decoded = unquote(value)
    if "/" in decoded or decoded.strip() in ("", ".", ".."):
        raise ValueError(
            f"Wajub: {name} {value!r} is not a Wajub id; "
            "an id is never empty and never contains '/'"
        )
    return quote(value, safe="")


def create_idempotency_key(prefix: str = "wajub") -> str:
    return f"{prefix}-{uuid.uuid4()}"


_IDEMPOTENCY_KEY_PARAMS = ("idempotencyKey", "idempotency_key")


def _given_values(candidates: dict[str, Any], what: str) -> dict[str, str]:
    """The values given among the candidates, by where they were given.

    A value is stripped, as the API does, and an empty or blank one counts as
    none. A value that is not a string raises a TypeError.
    """
    values: dict[str, str] = {}
    for where, value in candidates.items():
        if value is None:
            continue
        if not isinstance(value, str):
            raise TypeError(
                f"Wajub: the {what} in {where} must be a string, not {type(value).__name__}"
            )
        if value.strip():
            values[where] = value.strip()
    return values


def _idempotency_keys(candidates: dict[str, Any]) -> dict[str, str]:
    return _given_values(candidates, "idempotency key")


def _headers_named(options: RequestOptions, name: str) -> dict[str, Any]:
    return {
        f"the {key!r} header": value
        for key, value in (options.headers or {}).items()
        if key.lower() == name.lower()
    }


def request_options_sync(options: RequestOptions | None) -> str | None:
    """The account to act for, set in the request options, if any.

    It can be given as ``sync`` or as an X-Sync header, in any case; given more
    than once, it must be the same account. A blank one counts as none.
    """
    if options is None:
        return None
    given = _given_values(
        {"RequestOptions(sync=...)": options.sync, **_headers_named(options, "X-Sync")},
        "X-Sync value",
    )
    if len(set(given.values())) > 1:
        raise ValueError(
            "Wajub: RequestOptions carries two different X-Sync values "
            f"({' and '.join(given)}); pass it once, as RequestOptions(sync=...)"
        )
    return next(iter(given.values()), None)


def request_options_idempotency_key(options: RequestOptions | None) -> str | None:
    """The idempotency key set in the request options, if any.

    It can be given as ``idempotency_key`` or as an Idempotency-Key header, in
    any case; given more than once, it must be the same key. An empty or blank
    key counts as none, as in the params.
    """
    if options is None:
        return None
    given = _idempotency_keys(
        {
            "RequestOptions(idempotency_key=...)": options.idempotency_key,
            **_headers_named(options, "Idempotency-Key"),
        }
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
    given = _idempotency_keys(
        {f"params[{name!r}]": body.pop(name) for name in _IDEMPOTENCY_KEY_PARAMS if name in body}
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
