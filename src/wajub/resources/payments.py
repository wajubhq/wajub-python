"""Payments API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_list, pick_resource
from wajub.objects import Payment
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class PaymentsResource(BaseClient):
    def create(self, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        idempotency_key = params.pop("idempotencyKey", None)
        if idempotency_key and options is None:
            options = RequestOptions(idempotency_key=idempotency_key)
        elif idempotency_key and options:
            options = RequestOptions(
                idempotency_key=idempotency_key,
                headers=options.headers,
                sync=options.sync,
            )
        return self._to_payment_object(self.post("/payments", params, options))

    def initialize(self, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        return self.create(params, options)

    def retrieve(self, id: str) -> Payment:
        return Payment.from_dict(pick_resource(self.get(f"/payments/{id}"), "transaction"))

    def list(self, params: dict[str, Any] | None = None) -> PagedResult:
        return create_paged_list(self, "/payments", "transactions", params)

    def cancel(self, id: str, options: RequestOptions | None = None) -> Payment:
        return Payment.from_dict(
            pick_resource(self.request("DELETE", f"/payments/{id}", options=options), "transaction")
        )

    def process(self, id: str, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        return Payment.from_dict(
            pick_resource(self.post(f"/payments/{id}", params, options), "transaction")
        )

    def process_split(self, id: str, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        return Payment.from_dict(
            pick_resource(self.post(f"/payments/{id}/splits", params, options), "transaction")
        )

    def list_refunds(self, id: str, params: dict[str, Any] | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get(f"/payments/{id}/refunds", params), "refunds")

    def _to_payment_object(self, body: dict) -> Payment:
        transaction = pick_resource(body, "transaction")
        return Payment.from_dict(
            {
                **transaction,
                "authorization_token": str(
                    body.get("authorization_token")
                    or transaction.get("authorization_token")
                    or transaction.get("id")
                    or ""
                ),
                "authorization_url": str(
                    body.get("authorization_url") or transaction.get("authorization_url") or ""
                ),
            }
        )
