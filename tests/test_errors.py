"""Exception mapping tests."""

from __future__ import annotations

from wajub.errors import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    WajubError,
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


def test_field_errors_keep_every_message_of_each_field() -> None:
    err = error_from_response(
        422,
        {
            "message": "Validation failed",
            "errors": {
                "amount": ["Must be positive", "Must have at most 2 decimals"],
                "currency": ["Is required"],
                "email": "Is invalid",
            },
        },
    )
    assert isinstance(err, InvalidRequestError)
    assert err.field_errors == {
        "amount": ["Must be positive", "Must have at most 2 decimals"],
        "currency": ["Is required"],
        "email": ["Is invalid"],
    }
    # `errors` keeps its shape: the first message of each field.
    assert err.errors["amount"] == "Must be positive"
    assert err.errors["email"] == "Is invalid"


def test_a_field_with_no_message_is_left_out() -> None:
    # An empty list used to raise IndexError instead of the API's error.
    err = error_from_response(
        422, {"message": "Invalid", "errors": {"phone": [], "name": ["Too long"]}}
    )
    assert isinstance(err, InvalidRequestError)
    assert err.errors == {"name": "Too long"}
    assert err.field_errors == {"name": ["Too long"]}


def test_field_errors_is_none_without_errors_and_defaults_on_direct_construction() -> None:
    assert error_from_response(500, {"message": "Boom"}).field_errors is None
    assert WajubError("Boom").field_errors is None
    assert RateLimitError("Slow down", retry_after=3).field_errors is None
    err = InvalidRequestError(
        "Bad", "validation_error", 422, {"a": "x"}, {}, field_errors={"a": ["x", "y"]}
    )
    assert err.field_errors == {"a": ["x", "y"]}
