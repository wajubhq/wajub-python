"""Balance API resource."""

from __future__ import annotations

from wajub.http import BaseClient
from wajub.http_utils import pick_resource


class BalanceResource(BaseClient):
    def retrieve(self) -> dict:
        return pick_resource(self.get("/balance"), "balance", "data")
