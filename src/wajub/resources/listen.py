"""Listen API resource."""

from __future__ import annotations

from wajub.http import BaseClient
from wajub.http_utils import pick_resource
from wajub.request_options import RequestOptions


class ListenResource(BaseClient):
    def config(self) -> dict:
        return pick_resource(self.get("/listen/config"), "config", "listen")

    def auth(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post("/listen/auth", params, options), "auth", "listen")
