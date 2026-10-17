"""An id is one segment of the path: it can never reach another route."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from helpers import API_KEY, API_URL, make_client

from wajub.resources import (
    AccountsResource,
    BeneficiariesResource,
    CustomersResource,
    DisputesResource,
    EventsResource,
    InvoicesResource,
    LinksResource,
    PaymentsResource,
    RefundsResource,
    ShieldResource,
    TaxResource,
    TransfersResource,
    WebhookEndpointsResource,
)

Call = Callable[[Any, str], Any]

CRUD = {
    "accounts": AccountsResource,
    "beneficiaries": BeneficiariesResource,
    "customers": CustomersResource,
    "invoices": InvoicesResource,
    "links": LinksResource,
    "refunds": RefundsResource,
    "transfers": TransfersResource,
    "webhook_endpoints": WebhookEndpointsResource,
}

# Every method that puts an id in the path, with the id as its only variable.
CALLS: dict[str, tuple[type, Call]] = {
    **{f"{name}.retrieve": (cls, lambda r, i: r.retrieve(i)) for name, cls in CRUD.items()},
    **{f"{name}.update": (cls, lambda r, i: r.update(i, {"a": 1})) for name, cls in CRUD.items()},
    **{f"{name}.delete": (cls, lambda r, i: r.delete(i)) for name, cls in CRUD.items()},
    "payments.retrieve": (PaymentsResource, lambda r, i: r.retrieve(i)),
    "payments.cancel": (PaymentsResource, lambda r, i: r.cancel(i)),
    "payments.process": (PaymentsResource, lambda r, i: r.process(i, {"a": 1})),
    "payments.process_split": (PaymentsResource, lambda r, i: r.process_split(i, {"a": 1})),
    "payments.list_refunds": (PaymentsResource, lambda r, i: r.list_refunds(i)),
    "events.retrieve": (EventsResource, lambda r, i: r.retrieve(i)),
    "events.resend": (EventsResource, lambda r, i: r.resend(i)),
    "accounts.regenerate_token": (AccountsResource, lambda r, i: r.regenerate_token(i)),
    "customers.block": (CustomersResource, lambda r, i: r.block(i)),
    "customers.unblock": (CustomersResource, lambda r, i: r.unblock(i)),
    "customers.activate": (CustomersResource, lambda r, i: r.activate(i)),
    "customers.deactivate": (CustomersResource, lambda r, i: r.deactivate(i)),
    "customers.list_tax_ids": (CustomersResource, lambda r, i: r.list_tax_ids(i)),
    "customers.create_tax_id": (CustomersResource, lambda r, i: r.create_tax_id(i, {"a": 1})),
    "customers.delete_tax_id(customer_id)": (
        CustomersResource,
        lambda r, i: r.delete_tax_id(i, "txi_1"),
    ),
    "customers.delete_tax_id(tax_id)": (
        CustomersResource,
        lambda r, i: r.delete_tax_id("cus_1", i),
    ),
    "disputes.retrieve": (DisputesResource, lambda r, i: r.retrieve(i)),
    "disputes.submit_evidence": (DisputesResource, lambda r, i: r.submit_evidence(i, {"a": 1})),
    "disputes.accept": (DisputesResource, lambda r, i: r.accept(i)),
    "disputes.close": (DisputesResource, lambda r, i: r.close(i)),
    "disputes.send_message": (DisputesResource, lambda r, i: r.send_message(i, {"a": 1})),
    "shield.remove_from_blocklist": (ShieldResource, lambda r, i: r.remove_from_blocklist(i)),
    "webhook_endpoints.rotate_secret": (
        WebhookEndpointsResource,
        lambda r, i: r.rotate_secret(i),
    ),
    "invoices.send": (InvoicesResource, lambda r, i: r.send(i)),
    "invoices.mark_paid": (InvoicesResource, lambda r, i: r.mark_paid(i)),
    "invoices.cancel": (InvoicesResource, lambda r, i: r.cancel(i)),
    "tax.retrieve_code": (TaxResource, lambda r, i: r.retrieve_code(i)),
    "tax.retrieve_registration": (TaxResource, lambda r, i: r.retrieve_registration(i)),
    "tax.update_registration": (TaxResource, lambda r, i: r.update_registration(i, {"a": 1})),
    "tax.delete_registration": (TaxResource, lambda r, i: r.delete_registration(i)),
}


def _resource(cls: type, captured: list[httpx.Request]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"id": "obj_1"})

    return cls(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


@pytest.mark.parametrize(
    "bad_id",
    [
        "pay_1/refunds",
        "cus_1/tax_ids/txi_1",
        "/",
        "pay_1%2Frefunds",
        "pay_1%2frefunds",
        "",
        " ",
        ".",
        "..",
    ],
)
@pytest.mark.parametrize("call", sorted(CALLS))
def test_an_id_that_would_reach_another_route_is_refused_before_sending(
    call: str, bad_id: str
) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]

    with pytest.raises(ValueError, match="not a Wajub id"):
        send(_resource(cls, captured), bad_id)

    assert captured == []


@pytest.mark.parametrize("good_id", ["obj_9.x-Y", "trx.1..2", "..a", "a..", ".a"])
@pytest.mark.parametrize("call", sorted(CALLS))
def test_a_wajub_id_is_sent_in_the_path(call: str, good_id: str) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]

    send(_resource(cls, captured), good_id)

    assert len(captured) == 1
    assert f"/{good_id}" in captured[0].url.path


@pytest.mark.parametrize(
    "given, sent",
    [
        ("cus_1?", "cus_1%3F"),
        ("cus_1?expand=all", "cus_1%3Fexpand%3Dall"),
        ("cus_1#txi", "cus_1%23txi"),
        ("cus 1", "cus%201"),
        ("cus_1%41", "cus_1%2541"),
        ("trx.1..2", "trx.1..2"),
    ],
)
@pytest.mark.parametrize("call", sorted(CALLS))
def test_an_id_is_escaped_so_it_stays_one_segment(call: str, given: str, sent: str) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]

    send(_resource(cls, captured), given)

    assert len(captured) == 1
    raw = captured[0].url.raw_path.decode()
    assert f"/{sent}/" in f"{raw}/"
    assert "?" not in raw and "#" not in raw


def test_a_question_mark_cannot_turn_a_tax_id_deletion_into_a_customer_deletion() -> None:
    captured: list[httpx.Request] = []

    _resource(CustomersResource, captured).delete_tax_id("cus_1?", "txi_1")

    assert captured[0].method == "DELETE"
    assert captured[0].url.raw_path == b"/customers/cus_1%3F/tax_ids/txi_1"


@pytest.mark.parametrize("bad_id", [None, 42, b"pay_1", ["pay_1"]])
@pytest.mark.parametrize("call", sorted(CALLS))
def test_an_id_that_is_not_a_string_is_refused_before_sending(call: str, bad_id: object) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]

    with pytest.raises(TypeError, match="must be a string"):
        send(_resource(cls, captured), bad_id)

    assert captured == []


UPPER_UUID = "8F14E45F-CEEA-467F-A0E6-7A0C5F1B1E2D"
CANONICAL = "8f14e45f-ceea-467f-a0e6-7a0c5f1b1e2d"


@pytest.mark.parametrize("call", sorted(CALLS))
def test_a_uuid_id_is_sent_in_its_canonical_form(call: str) -> None:
    captured: list[httpx.Request] = []
    cls, send = CALLS[call]

    send(_resource(cls, captured), uuid.UUID(UPPER_UUID))

    assert len(captured) == 1
    assert f"/{CANONICAL}/" in f"{captured[0].url.raw_path.decode()}/"


@pytest.mark.parametrize(
    "cls, send, method, path",
    [
        (
            WebhookEndpointsResource,
            lambda r, i: r.delete(i),
            "DELETE",
            f"/webhooks/{CANONICAL}",
        ),
        (
            CustomersResource,
            lambda r, i: r.delete_tax_id("cus_1", i),
            "DELETE",
            f"/customers/cus_1/tax_ids/{CANONICAL}",
        ),
        (
            TaxResource,
            lambda r, i: r.retrieve_registration(i),
            "GET",
            f"/tax/registrations/{CANONICAL}",
        ),
        (
            ShieldResource,
            lambda r, i: r.remove_from_blocklist(i),
            "DELETE",
            f"/shield/blocklist/{CANONICAL}",
        ),
    ],
)
def test_the_resources_with_uuid_ids_take_a_uuid(
    cls: type, send: Call, method: str, path: str
) -> None:
    captured: list[httpx.Request] = []

    send(_resource(cls, captured), uuid.UUID(UPPER_UUID))

    assert captured[0].method == method
    assert captured[0].url.raw_path == path.encode()
