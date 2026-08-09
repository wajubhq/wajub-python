"""Shield API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_list, pick_resource
from wajub.request_options import RequestOptions


class ShieldResource(BaseClient):
    def get_settings(self) -> dict:
        return pick_resource(self.get("/shield/settings"), "shield", "settings")

    def update_settings(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.put("/shield/settings", params, options), "shield", "settings")

    def stats(self, params: dict | None = None) -> dict:
        return pick_resource(self.get("/shield/stats", params), "shield", "stats")

    def list_blocklist(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/shield/blocklist", params), "blocklist", "entries")

    def add_to_blocklist(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post("/shield/blocklist", params, options), "blocklist", "entry")

    def remove_from_blocklist(self, id: str, options: RequestOptions | None = None) -> None:
        self.request("DELETE", f"/shield/blocklist/{id}", options=options)
