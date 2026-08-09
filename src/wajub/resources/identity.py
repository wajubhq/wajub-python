"""Identity API resource."""

from __future__ import annotations

from wajub.http import BaseClient
from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions


class IdentityResource(BaseClient):
    def resolve(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post("/identity/resolve", params, options), "identity")

    def validate(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post("/identity/validate", params, options), "identity")
