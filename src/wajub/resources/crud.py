"""Generic CRUD resource base."""

from __future__ import annotations

from typing import Any

import httpx

from wajub.http import BaseClient
from wajub.http_utils import idempotency_key_from_params, path_id, pick_resource
from wajub.objects import ApiObject
from wajub.request_options import RequestOptions
from wajub.resources.pagination import PagedResult, create_paged_list


class CrudResource(BaseClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        path: str,
        singular: str,
        plural: str,
        idempotency_key_prefix: str = "wajub",
        client: httpx.Client | None = None,
        object_class: type[ApiObject] = ApiObject,
        max_network_retries: int | None = None,
    ) -> None:
        super().__init__(api_key, base_url, idempotency_key_prefix, client, max_network_retries)
        self._path = path
        self._singular = singular
        self._plural = plural
        self._object_class = object_class

    def create(self, params: dict[str, Any], options: RequestOptions | None = None) -> ApiObject:
        body, options = idempotency_key_from_params(params, options)
        data = pick_resource(self.post(f"/{self._path}", body, options), self._singular)
        return self._object_class.from_dict(data)

    def retrieve(self, id: str) -> ApiObject:
        data = pick_resource(self.get(f"/{self._path}/{path_id(id)}"), self._singular)
        return self._object_class.from_dict(data)

    def list(self, params: dict[str, Any] | None = None) -> PagedResult:
        return create_paged_list(self, f"/{self._path}", self._plural, params)

    def update(
        self, id: str, params: dict[str, Any], options: RequestOptions | None = None
    ) -> ApiObject:
        data = pick_resource(
            self.put(f"/{self._path}/{path_id(id)}", params, options), self._singular
        )
        return self._object_class.from_dict(data)

    def delete(self, id: str, options: RequestOptions | None = None) -> None:
        self.request("DELETE", f"/{self._path}/{path_id(id)}", options=options)
