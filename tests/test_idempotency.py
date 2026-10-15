"""An idempotency key given in the params of any create goes out as the header."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from helpers import API_KEY, API_URL, make_client

from wajub.http import BaseClient
from wajub.request_options import RequestOptions
from wajub.resources import (
    AccountsResource,
    BeneficiariesResource,
    CustomersResource,
    InvoicesResource,
    LinksResource,
    PaymentsResource,
    RefundsResource,
    TaxResource,
    TransfersResource,
    WebhookEndpointsResource,
)

Call = Callable[[Any, dict[str, Any], RequestOptions | None], Any]

# Every method that sends the caller's params in a POST the API can replay.
CALLS: dict[str, tuple[type, Call]] = {
    "payments.create": (PaymentsResource, lambda r, p, o: r.create(p, o)),
    "payments.process": (PaymentsResource, lambda r, p, o: r.process("pay_1", p, o)),
    "payments.process_split": (PaymentsResource, lambda r, p, o: r.process_split("pay_1", p, o)),
    "refunds.create": (RefundsResource, lambda r, p, o: r.create(p, o)),
    "transfers.create": (TransfersResource, lambda r, p, o: r.create(p, o)),
    "customers.create": (CustomersResource, lambda r, p, o: r.create(p, o)),
    "customers.create_tax_id": (
        CustomersResource,
        lambda r, p, o: r.create_tax_id("cus_1", p, o),
    ),
    "beneficiaries.create": (BeneficiariesResource, lambda r, p, o: r.create(p, o)),
    "links.create": (LinksResource, lambda r, p, o: r.create(p, o)),
    "invoices.create": (InvoicesResource, lambda r, p, o: r.create(p, o)),
    "accounts.create": (AccountsResource, lambda r, p, o: r.create(p, o)),
    "webhook_endpoints.create": (WebhookEndpointsResource, lambda r, p, o: r.create(p, o)),
    "tax.create_registration": (TaxResource, lambda r, p, o: r.create_registration(p, o)),
}


def _resource(cls: type, captured: list[httpx.Request]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"id": "obj_1"})

    return cls(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


@pytest.mark.parametrize("name", ["idempotencyKey", "idempotency_key"])
@pytest.mark.parametrize("call", sorted(CALLS))
def test_a_key_in_params_is_sent_as_the_header_and_left_in_the_callers_dict(
    call: str, name: str
) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]
    resource = _resource(cls, captured)
    params = {"amount": 5000, name: "order-42"}

    send(resource, params, RequestOptions(sync="acct_ref"))
    send(resource, params, None)

    assert [r.headers["Idempotency-Key"] for r in captured] == ["order-42", "order-42"]
    assert captured[0].headers["X-Sync"] == "acct_ref"
    assert json.loads(captured[0].read()) == {"amount": 5000}
    assert params == {"amount": 5000, name: "order-42"}


def test_refunds_create_sends_the_key_once_for_a_retried_refund() -> None:
    captured: list[httpx.Request] = []
    refunds = _resource(RefundsResource, captured)
    params = {"payment": "pay_1", "amount": 1000, "idempotencyKey": "refund-order-42"}

    refunds.create(params)
    refunds.create(params)

    assert [r.headers["Idempotency-Key"] for r in captured] == ["refund-order-42"] * 2
    assert "idempotencyKey" not in captured[0].read().decode()


def test_transfers_create_refuses_a_key_that_differs_from_request_options() -> None:
    captured: list[httpx.Request] = []
    transfers = _resource(TransfersResource, captured)

    with pytest.raises(ValueError, match="idempotency key"):
        transfers.create(
            {"amount": 1000, "idempotency_key": "payout-1"},
            RequestOptions(idempotency_key="payout-2"),
        )
    with pytest.raises(ValueError, match="idempotency key"):
        transfers.create({"amount": 1000, "idempotencyKey": "a", "idempotency_key": "b"})
    with pytest.raises(TypeError, match="idempotency key"):
        transfers.create({"amount": 1000, "idempotencyKey": 42})

    assert captured == []


def test_transfers_create_accepts_the_same_key_in_params_and_options() -> None:
    captured: list[httpx.Request] = []
    transfers = _resource(TransfersResource, captured)

    transfers.create(
        {"amount": 1000, "idempotency_key": "payout-1"},
        RequestOptions(idempotency_key="payout-1", headers={"X-Trace": "t1"}),
    )

    assert captured[0].headers["Idempotency-Key"] == "payout-1"
    assert captured[0].headers["X-Trace"] == "t1"


@pytest.mark.parametrize("call", sorted(CALLS))
def test_without_a_key_in_params_each_call_still_gets_its_own_key(call: str) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]
    resource = _resource(cls, captured)

    send(resource, {"amount": 5000}, None)
    send(resource, {"amount": 5000}, RequestOptions(idempotency_key="mine"))

    assert captured[0].headers["Idempotency-Key"].startswith("wajub-")
    assert captured[1].headers["Idempotency-Key"] == "mine"


def _base_client(captured: list[httpx.Request]) -> BaseClient:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"id": "obj_1"})

    return BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


@pytest.mark.parametrize("header", ["Idempotency-Key", "idempotency-key", "IDEMPOTENCY-KEY"])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_an_idempotency_key_header_in_request_options_is_sent_as_given(
    header: str, method: str
) -> None:
    captured: list[httpx.Request] = []
    client = _base_client(captured)

    client.request(method, "/payments", options=RequestOptions(headers={header: "order-42"}))

    assert captured[0].headers.get_list("Idempotency-Key") == ["order-42"]


def test_the_same_key_as_header_and_idempotency_key_is_sent_once() -> None:
    captured: list[httpx.Request] = []
    client = _base_client(captured)

    client.post(
        "/payments",
        {"amount": 5000},
        RequestOptions(idempotency_key="order-42", headers={"idempotency-key": "order-42"}),
    )

    assert captured[0].headers.get_list("Idempotency-Key") == ["order-42"]


def test_a_header_that_differs_from_idempotency_key_is_refused() -> None:
    captured: list[httpx.Request] = []
    client = _base_client(captured)

    with pytest.raises(ValueError, match="idempotency key"):
        client.post(
            "/payments",
            {"amount": 5000},
            RequestOptions(idempotency_key="order-42", headers={"Idempotency-Key": "order-43"}),
        )
    with pytest.raises(ValueError, match="idempotency key"):
        client.post(
            "/payments",
            {"amount": 5000},
            RequestOptions(headers={"Idempotency-Key": "a", "idempotency-key": "b"}),
        )

    assert captured == []


def test_a_header_key_and_a_params_key_must_match() -> None:
    captured: list[httpx.Request] = []
    refunds = _resource(RefundsResource, captured)

    with pytest.raises(ValueError, match="idempotency key"):
        refunds.create(
            {"payment": "pay_1", "idempotencyKey": "refund-1"},
            RequestOptions(headers={"Idempotency-Key": "refund-2"}),
        )
    assert captured == []

    refunds.create(
        {"payment": "pay_1", "idempotencyKey": "refund-1"},
        RequestOptions(headers={"Idempotency-Key": "refund-1"}),
    )
    assert captured[0].headers.get_list("Idempotency-Key") == ["refund-1"]
