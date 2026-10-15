"""Tax API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import idempotency_key_from_params, pick_list, pick_resource
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class TaxResource(BaseClient):
    def get_settings(self) -> dict:
        return pick_resource(self.get("/tax/settings"), "tax", "settings")

    def update_settings(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.put("/tax/settings", params, options), "tax", "settings")

    def rates(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/rates", params), "rates", "tax_rates")

    def calculate(self, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(self.post("/tax/calculate", params, options), "tax", "calculation")

    def reports(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/reports", params), "reports", "tax_reports")

    def list_codes(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/codes", params), "tax_codes", "codes")

    def retrieve_code(self, code: str) -> dict:
        return pick_resource(self.get(f"/tax/codes/{code}"), "tax_code", "code")

    def list_registrations(self, params: dict | None = None) -> PagedResult:
        return create_paged_list(self, "/tax/registrations", "registrations", params)

    def create_registration(self, params: dict, options: RequestOptions | None = None) -> dict:
        body, options = idempotency_key_from_params(params, options)
        return pick_resource(
            self.post("/tax/registrations", body, options), "registration", "tax_registration"
        )

    def retrieve_registration(self, id: str) -> dict:
        return pick_resource(
            self.get(f"/tax/registrations/{id}"), "registration", "tax_registration"
        )

    def update_registration(self, id: str, params: dict, options: RequestOptions | None = None) -> dict:
        return pick_resource(
            self.put(f"/tax/registrations/{id}", params, options), "registration", "tax_registration"
        )

    def delete_registration(self, id: str, options: RequestOptions | None = None) -> None:
        self.request("DELETE", f"/tax/registrations/{id}", options=options)

    def jurisdictions(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/jurisdictions", params), "jurisdictions", "tax_jurisdictions")

    def thresholds(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/thresholds", params), "thresholds", "tax_thresholds")

    def threshold_alerts(self, params: dict | None = None) -> tuple[list, dict | None]:
        return pick_list(self.get("/tax/thresholds/alerts", params), "alerts", "threshold_alerts")
