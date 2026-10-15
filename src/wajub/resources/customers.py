"""Customers API resource."""

from __future__ import annotations

from typing import Any

import httpx

from wajub.http_utils import idempotency_key_from_params, pick_list, pick_resource
from wajub.objects import Customer
from wajub.request_options import RequestOptions
from wajub.resources.crud import CrudResource


class CustomersResource(CrudResource):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(
            api_key, base_url, "customers", "customer", "customers", prefix, client, Customer,
            max_network_retries=max_network_retries,
        )

    def block(self, id: str, params: dict | None = None, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/customers/{id}/block", params, options), "customer")

    def unblock(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/customers/{id}/unblock", None, options), "customer")

    def activate(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/customers/{id}/activate", None, options), "customer")

    def deactivate(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/customers/{id}/deactivate", None, options), "customer")

    def list_tax_ids(self, customer_id: str) -> tuple[list, dict | None]:
        return pick_list(self.get(f"/customers/{customer_id}/tax_ids"), "tax_ids")

    def create_tax_id(
        self, customer_id: str, params: dict[str, Any], options: RequestOptions | None = None
    ) -> dict:
        body, options = idempotency_key_from_params(params, options)
        return pick_resource(
            self.post(f"/customers/{customer_id}/tax_ids", body, options), "tax_id"
        )

    def delete_tax_id(self, customer_id: str, tax_id: str, options: RequestOptions | None = None) -> None:
        self.request("DELETE", f"/customers/{customer_id}/tax_ids/{tax_id}", options=options)
