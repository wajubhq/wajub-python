"""An id is one segment of the path: it can never reach another route."""

from __future__ import annotations

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
    ["pay_1/refunds", "cus_1/tax_ids/txi_1", "/", "pay_1%2Frefunds", "pay_1%2frefunds", "",
     " ", ".", ".."],
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
