"""Disputes API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class DisputesResource(BaseClient):
    def list(self, params: dict[str, Any] | None = None) -> PagedResult:
        return create_paged_list(self, "/disputes", "disputes", params)

    def retrieve(self, id: str) -> dict:
        return pick_resource(self.get(f"/disputes/{id}"), "dispute")

    def submit_evidence(self, id: str, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(
            self.post(f"/disputes/{id}/submit-evidence", params, options), "dispute"
        )

    def accept(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/disputes/{id}/accept", None, options), "dispute")

    def close(self, id: str, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/disputes/{id}/close", None, options), "dispute")

    def send_message(self, id: str, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post(f"/disputes/{id}/messages", params, options), "dispute")
