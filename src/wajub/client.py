"""Wajub server SDK client."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Any

import httpx

from wajub.version import __version__
from wajub.http_utils import API_URL, normalize_api_key
from wajub.resources import (
    AccountsResource,
    BalanceResource,
    BeneficiariesResource,
    CustomersResource,
    DisputesResource,
    EventsResource,
    GlobalResource,
    IdentityResource,
    InvoicesResource,
    LinksResource,
    ListenResource,
    PaymentsResource,
    RefundsResource,
    ShieldResource,
    TaxResource,
    TransfersResource,
    WebhookEndpointsResource,
)
from wajub.webhooks import Webhooks


def _default_http_client(base_url: str) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        timeout=30.0,
        headers={"User-Agent": f"wajub-python/{__version__}"},
    )


class Wajub:
    """
    Wajub server SDK — Stripe-like entry point for Python 3.10+.

    ```python
    from wajub import Wajub

    with Wajub(api_key=os.environ["WAJUB_API_KEY"]) as wajub:
        payment = wajub.payments.create({
            "amount": 15000,
            "currency": "XAF",
            "email": "buyer@example.com",
            "callback": "https://shop.example.com/complete",
        })
    ```
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        webhook_secret: str | None = None,
        idempotency_key_prefix: str = "wajub",
        http_client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        key = normalize_api_key(
            api_key or os.environ.get("WAJUB_API_KEY") or ""
        )
        if not key:
            raise ValueError("Wajub: api_key is required")

        base_url = API_URL
        prefix = idempotency_key_prefix
        self._owns_http = http_client is None
        self._http = http_client or _default_http_client(base_url)

        self.global_ = GlobalResource(key, base_url, prefix, self._http, max_network_retries)
        self.payments = PaymentsResource(key, base_url, prefix, self._http, max_network_retries)
        self.customers = CustomersResource(key, base_url, prefix, self._http, max_network_retries)
        self.refunds = RefundsResource(key, base_url, prefix, self._http, max_network_retries)
        self.transfers = TransfersResource(key, base_url, prefix, self._http, max_network_retries)
        self.beneficiaries = BeneficiariesResource(key, base_url, prefix, self._http, max_network_retries)
        self.links = LinksResource(key, base_url, prefix, self._http, max_network_retries)
        self.balance = BalanceResource(key, base_url, prefix, self._http, max_network_retries)
        self.events = EventsResource(key, base_url, prefix, self._http, max_network_retries)
        self.accounts = AccountsResource(key, base_url, prefix, self._http, max_network_retries)
        self.webhook_endpoints = WebhookEndpointsResource(key, base_url, prefix, self._http, max_network_retries)
        self.invoices = InvoicesResource(key, base_url, prefix, self._http, max_network_retries)
        self.disputes = DisputesResource(key, base_url, prefix, self._http, max_network_retries)
        self.identity = IdentityResource(key, base_url, prefix, self._http, max_network_retries)
        self.tax = TaxResource(key, base_url, prefix, self._http, max_network_retries)
        self.shield = ShieldResource(key, base_url, prefix, self._http, max_network_retries)
        self.listen = ListenResource(key, base_url, prefix, self._http, max_network_retries)

        wh_secret = webhook_secret or os.environ.get("WAJUB_WEBHOOK_SECRET", "")
        self.webhooks = Webhooks(wh_secret)

    def __getattr__(self, name: str) -> Any:
        if name == "global":
            return self.global_
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Wajub:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
