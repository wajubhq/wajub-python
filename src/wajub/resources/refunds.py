"""Refunds API resource."""

from __future__ import annotations

import httpx

from wajub.objects import Refund
from wajub.resources.crud import CrudResource


class RefundsResource(CrudResource):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(
            api_key, base_url, "refunds", "refund", "refunds", prefix, client, Refund,
            max_network_retries=max_network_retries,
        )
