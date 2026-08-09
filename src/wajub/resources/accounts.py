"""Accounts API resource."""

from __future__ import annotations

import httpx

from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions
from wajub.resources.crud import CrudResource


class AccountsResource(CrudResource):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(
            api_key, base_url, "accounts", "account", "accounts", prefix, client, max_network_retries=max_network_retries
        )

    def regenerate_token(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/accounts/{id}/token", None, options), "account")
