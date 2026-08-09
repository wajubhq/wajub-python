"""Global API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import pick_list


class GlobalResource(BaseClient):
    def ping(self) -> dict:
        return self.get("/")

    def channels(self, params: dict[str, Any] | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/channels", params), "channels")

    def countries(self, params: dict[str, Any] | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/countries", params), "countries")

    def currencies(self, params: dict[str, Any] | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/currencies", params), "currencies")
