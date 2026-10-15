"""HTTP utilities tests."""

from __future__ import annotations

from wajub.errors import WajubError
from wajub.http_utils import (
    create_idempotency_key,
    error_from_response,
    normalize_api_key,
    pick_list,
    pick_resource,
)


def test_normalize_api_key_strips_bearer_prefix() -> None:
    assert normalize_api_key("Bearer sk_test.abc") == "sk_test.abc"
    assert normalize_api_key("bearer pk_test.abc") == "pk_test.abc"
    assert normalize_api_key("rk_test.abc") == "rk_test.abc"


def test_pick_resource_returns_first_matching_key() -> None:
    body = {"transaction": {"id": "pay_123", "amount": 5000}}
    assert pick_resource(body, "transaction")["id"] == "pay_123"


def test_pick_resource_falls_back_to_body() -> None:
    assert pick_resource({"id": "pay_123"}, "transaction")["id"] == "pay_123"


def test_pick_list_extracts_plural_key_and_meta() -> None:
    data, meta = pick_list(
        {"refunds": [{"id": "ref_1"}], "meta": {"current_page": 1}},
        "refunds",
    )
    assert data[0]["id"] == "ref_1"
    assert meta is not None and meta["current_page"] == 1


def test_pick_list_falls_back_to_data_key() -> None:
    data, meta = pick_list({"data": [{"id": "x"}], "meta": {"total": 1}}, "missing")
    assert data[0]["id"] == "x"


def test_create_idempotency_key_has_prefix() -> None:
    assert create_idempotency_key().startswith("wajub-")
    assert create_idempotency_key("custom").startswith("custom-")


def test_error_from_response_builds_wajub_error() -> None:
    err = error_from_response(
        422,
        {
            "message": "Validation failed",
            "code": "validation_error",
            "errors": {"amount": ["Must be positive"]},
        },
    )
    assert isinstance(err, WajubError)
    assert err.message == "Validation failed"
    assert err.code == "validation_error"
    assert err.http_status == 422
    assert err.errors is not None and err.errors["amount"] == "Must be positive"
