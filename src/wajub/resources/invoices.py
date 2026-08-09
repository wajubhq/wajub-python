"""Invoices API resource."""

from __future__ import annotations

import httpx

from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions
from wajub.resources.crud import CrudResource


class InvoicesResource(CrudResource):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(
            api_key, base_url, "invoices", "invoice", "invoices", prefix, client,
            max_network_retries=max_network_retries,
        )

    def send(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/invoices/{id}/send", None, options), "invoice")

    def mark_paid(
        self, id: str, params: dict | None = None, options: RequestOptions | None = None
    ) -> dict:
        return pick_resource(self.post(f"/invoices/{id}/mark-paid", params, options), "invoice")

    def cancel(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/invoices/{id}/cancel", None, options), "invoice")
