"""Events API resource."""

from __future__ import annotations

from typing import Any

from wajub.http import BaseClient
from wajub.http_utils import path_id, pick_resource
from wajub.objects import Event
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class EventsResource(BaseClient):
    def list(self, params: dict[str, Any] | None = None) -> PagedResult:
        return create_paged_list(self, "/events", "events", params)

    def retrieve(self, id: str) -> Event:
        return Event.from_dict(pick_resource(self.get(f"/events/{path_id(id)}"), "event"))

    def resend(self, id: str, options: RequestOptions | None = None) -> Event:
        return Event.from_dict(
            pick_resource(self.post(f"/events/{path_id(id)}/resend", None, options), "event")
        )
