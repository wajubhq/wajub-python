"""Exception mapping tests."""

from __future__ import annotations

from wajub.errors import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
)
from wajub.http_utils import error_from_response


def test_maps_401_to_authentication_error() -> None:
    err = error_from_response(401, {"message": "Unauthorized", "code": "auth_error"})
    assert isinstance(err, AuthenticationError)
    assert err.http_status == 401


def test_maps_403_to_permission_error() -> None:
    err = error_from_response(403, {"message": "Forbidden"})
    assert isinstance(err, PermissionError)


def test_maps_404_to_not_found_error() -> None:
    err = error_from_response(404, {"message": "Not found"})
    assert isinstance(err, NotFoundError)


def test_maps_422_to_invalid_request_error() -> None:
    err = error_from_response(422, {"message": "Validation failed", "code": "validation_error"})
    assert isinstance(err, InvalidRequestError)
    assert err.code == "validation_error"


def test_maps_429_to_rate_limit_error_with_retry_after() -> None:
    err = error_from_response(429, {"message": "Too many requests"}, retry_after=30)
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 30
