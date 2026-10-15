"""Resource layer tests."""

from __future__ import annotations

import httpx
import pytest

from wajub.objects import Payment
from wajub.request_options import RequestOptions
from wajub.resources import PaymentsResource, RefundsResource
from helpers import API_KEY, API_URL, make_client


def test_payments_create_unwraps_transaction_and_urls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "transaction": {"id": "pay_123", "status": "pending"},
                "authorization_token": "tok_abc",
                "authorization_url": "https://checkout.test/pay/pay_123",
            },
        )

    payments = PaymentsResource(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    payment = payments.create({"amount": 5000, "currency": "XAF"})

    assert isinstance(payment, Payment)
    assert payment.id == "pay_123"
    assert payment.authorization_token == "tok_abc"
    assert payment.authorization_url == "https://checkout.test/pay/pay_123"
    assert payment["id"] == "pay_123"
    assert payment["authorization_token"] == "tok_abc"
    assert payment["authorization_url"] == "https://checkout.test/pay/pay_123"


def _capturing_payments(captured: list[httpx.Request]) -> PaymentsResource:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"transaction": {"id": "pay_1", "status": "pending"}})

    return PaymentsResource(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


@pytest.mark.parametrize("name", ["idempotencyKey", "idempotency_key"])
def test_payments_create_sends_an_idempotency_key_given_in_params(name: str) -> None:
    captured: list[httpx.Request] = []
    payments = _capturing_payments(captured)
    params = {"amount": 5000, "currency": "XAF", name: "order-42"}

    payments.create(params, RequestOptions(sync="acct_ref"))

    assert captured[0].headers["Idempotency-Key"] == "order-42"
    assert captured[0].headers["X-Sync"] == "acct_ref"
    assert name not in captured[0].read().decode()


def test_payments_create_keeps_the_key_in_the_callers_params_for_a_retry() -> None:
    captured: list[httpx.Request] = []
    payments = _capturing_payments(captured)
    params = {"amount": 5000, "currency": "XAF", "idempotencyKey": "order-42"}

    payments.create(params)
    payments.create(params)

    assert params["idempotencyKey"] == "order-42"
    assert [r.headers["Idempotency-Key"] for r in captured] == ["order-42", "order-42"]


def test_payments_create_refuses_two_different_idempotency_keys() -> None:
    captured: list[httpx.Request] = []
    payments = _capturing_payments(captured)

    with pytest.raises(ValueError, match="idempotency key"):
        payments.create(
            {"amount": 5000, "currency": "XAF", "idempotencyKey": "order-42"},
            RequestOptions(idempotency_key="order-43"),
        )
    with pytest.raises(ValueError, match="idempotency key"):
        payments.create(
            {"amount": 5000, "currency": "XAF", "idempotencyKey": "a", "idempotency_key": "b"}
        )

    assert captured == []


def test_payments_create_accepts_the_same_key_in_params_and_options() -> None:
    captured: list[httpx.Request] = []
    payments = _capturing_payments(captured)

    payments.create(
        {"amount": 5000, "currency": "XAF", "idempotencyKey": "order-42"},
        RequestOptions(idempotency_key="order-42"),
    )

    assert captured[0].headers["Idempotency-Key"] == "order-42"


def test_payments_create_refuses_an_idempotency_key_that_is_not_a_string() -> None:
    payments = _capturing_payments([])

    with pytest.raises(TypeError, match="idempotency key"):
        payments.create({"amount": 5000, "currency": "XAF", "idempotencyKey": 42})


def test_payments_retrieve() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"transaction": {"id": "pay_789", "status": "succeeded"}})

    payments = PaymentsResource(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    payment = payments.retrieve("pay_789")
    assert payment.status == "succeeded"
    assert payment["status"] == "succeeded"


def test_payments_list_pagination() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                200,
                json={
                    "transactions": [{"id": "pay_1"}],
                    "meta": {"current_page": 1, "last_page": 2},
                },
            )
        return httpx.Response(
            200,
            json={
                "transactions": [{"id": "pay_2"}],
                "meta": {"current_page": 2, "last_page": 2},
            },
        )

    payments = PaymentsResource(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    page1 = payments.list({"per_page": 1})
    assert page1.data[0]["id"] == "pay_1"
    assert page1.has_more is True

    page2 = page1.get_next_page()
    assert page2.data[0]["id"] == "pay_2"
    assert page2.has_more is False


def test_refunds_crud() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if request.method == "POST":
            return httpx.Response(200, json={"refund": {"id": "ref_new"}})
        if request.method == "GET":
            return httpx.Response(200, json={"refund": {"id": "ref_new", "status": "pending"}})
        return httpx.Response(200, json={})

    refunds = RefundsResource(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    created = refunds.create({"payment_id": "pay_1", "amount": 500})
    assert created["id"] == "ref_new"

    retrieved = refunds.retrieve("ref_new")
    assert retrieved["status"] == "pending"

    refunds.delete("ref_new")
