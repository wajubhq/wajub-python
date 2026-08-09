"""Resource layer tests."""

from __future__ import annotations

import httpx

from wajub.objects import Payment
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


def test_payments_initialize_is_alias_for_create() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "transaction": {"id": "pay_456"},
                "authorization_url": "https://checkout.test/pay/pay_456",
            },
        )

    payments = PaymentsResource(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    payment = payments.initialize({"amount": 1000, "currency": "XAF"})
    assert payment.id == "pay_456"
    assert payment["id"] == "pay_456"


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
