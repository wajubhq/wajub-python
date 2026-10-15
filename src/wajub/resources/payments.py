"""Payments API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import idempotency_key_from_params, path_id, pick_list, pick_resource
from wajub.objects import Payment
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class PaymentsResource(BaseClient):
    def create(self, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        body, options = idempotency_key_from_params(params, options)
        return self._to_payment_object(self.post("/payments", body, options))

    def retrieve(self, id: str) -> Payment:
        return Payment.from_dict(pick_resource(self.get(f"/payments/{path_id(id)}"), "transaction"))

    def list(self, params: dict[str, Any] | None = None) -> PagedResult:
        return create_paged_list(self, "/payments", "transactions", params)

    def cancel(self, id: str, options: RequestOptions | None = None) -> Payment:
        body = self.request("DELETE", f"/payments/{path_id(id)}", options=options)
        return Payment.from_dict(pick_resource(body, "transaction"))

    def process(
        self, id: str, params: dict[str, Any], options: RequestOptions | None = None
    ) -> Payment:
        body, options = idempotency_key_from_params(params, options)
        return Payment.from_dict(
            pick_resource(self.post(f"/payments/{path_id(id)}", body, options), "transaction")
        )

    def process_split(
        self, id: str, params: dict[str, Any], options: RequestOptions | None = None
    ) -> Payment:
        body, options = idempotency_key_from_params(params, options)
        return Payment.from_dict(
            pick_resource(
                self.post(f"/payments/{path_id(id)}/splits", body, options), "transaction"
            )
        )

    def list_refunds(
        self, id: str, params: dict[str, Any] | None = None
    ) -> tuple[list, dict | None]:
        return pick_list(self.get(f"/payments/{path_id(id)}/refunds", params), "refunds")

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
