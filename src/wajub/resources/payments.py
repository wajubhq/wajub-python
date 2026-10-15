"""Payments API resource."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_list, pick_resource
from wajub.objects import Payment
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list

_IDEMPOTENCY_KEY_PARAMS = ("idempotencyKey", "idempotency_key")


def _idempotency_key_from_params(
    body: dict[str, Any], options: RequestOptions | None
) -> RequestOptions | None:
    """Move an idempotency key given in the params to the request options.

    The key is sent as the Idempotency-Key header, never in the body, and the
    caller's dict is left as it was so that the same params can be sent again.
    """
    keys = {name: body.pop(name) for name in _IDEMPOTENCY_KEY_PARAMS if name in body}
    given = {name: key for name, key in keys.items() if key is not None and key != ""}
    for name, key in given.items():
        if not isinstance(key, str):
            raise TypeError(
                f"Wajub: the idempotency key in params[{name!r}] must be a string, "
                f"not {type(key).__name__}"
            )
    if len(set(given.values())) > 1:
        raise ValueError(
            "Wajub: params has two different idempotency keys "
            "('idempotencyKey' and 'idempotency_key'); pass one"
        )
    if not given:
        return options

    key = next(iter(given.values()))
    if options is None:
        return RequestOptions(idempotency_key=key)
    if options.idempotency_key is not None and options.idempotency_key != key:
        raise ValueError(
            "Wajub: params and RequestOptions carry two different idempotency keys; "
            "pass it once, as RequestOptions(idempotency_key=...)"
        )
    return replace(options, idempotency_key=key)


class PaymentsResource(BaseClient):
    def create(self, params: dict[str, Any], options: RequestOptions | None = None) -> Payment:
        body = dict(params)
        options = _idempotency_key_from_params(body, options)
        return self._to_payment_object(self.post("/payments", body, options))

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
