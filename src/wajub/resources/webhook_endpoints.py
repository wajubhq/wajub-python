"""Webhook endpoints API resource."""

from __future__ import annotations

import httpx

from wajub.http_utils import path_id, pick_resource
from wajub.request_options import RequestOptions
from wajub.resources.crud import CrudResource


class WebhookEndpointsResource(CrudResource):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(
            api_key, base_url, "webhooks", "endpoint", "endpoints", prefix, client,
            max_network_retries=max_network_retries,
        )

    def rotate_secret(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(
            self.post(f"/webhooks/{path_id(id)}/rotate-secret", None, options), "endpoint"
        )
