"""Base HTTP client for the Wajub merchant API."""

from __future__ import annotations

import time
from typing import Any

import httpx

from wajub.errors import ApiConnectionError
from wajub.http_utils import (
    create_idempotency_key,
    error_from_response,
    normalize_api_key,
)
from wajub.request_options import RequestOptions
from wajub.retry import (
    MAX_RETRIES,
    delay_seconds,
    idempotency_conflict_delay_seconds,
    is_idempotency_key_in_progress,
    parse_retry_after,
    should_retry_status,
)


class BaseClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        idempotency_key_prefix: str = "wajub",
        client: httpx.Client | None = None,
        max_network_retries: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.idempotency_key_prefix = idempotency_key_prefix
        self._client = client or httpx.Client(base_url=self.base_url, timeout=30.0)
        self.max_network_retries = (
            max_network_retries if max_network_retries is not None else MAX_RETRIES
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        return self.request("GET", path, query=params)

    def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> dict:
        return self.request("POST", path, body=body, options=options)

    def put(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> dict:
        return self.request("PUT", path, body=body, options=options)

    def delete(self, path: str, options: RequestOptions | None = None) -> dict:
        return self.request("DELETE", path, options=options)

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        options: RequestOptions | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Authorization": normalize_api_key(self.api_key),
        }

        if options and options.headers:
            headers.update(options.headers)

        if options and options.sync:
            headers["X-Sync"] = options.sync

        idempotency_key = options.idempotency_key if options else None
        if idempotency_key is None and method not in ("GET", "DELETE"):
            idempotency_key = create_idempotency_key(self.idempotency_key_prefix)

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        kwargs: dict[str, Any] = {"headers": headers}
        if query:
            kwargs["params"] = {k: v for k, v in query.items() if v is not None}
        if body is not None:
            headers["Content-Type"] = "application/json"
            kwargs["json"] = body

        attempt = 0

        while True:
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.HTTPError as exc:
                if attempt < self.max_network_retries:
                    attempt += 1
                    time.sleep(delay_seconds(attempt))
                    continue
                raise ApiConnectionError(str(exc), "network_error") from exc

            try:
                data = response.json()
            except Exception:
                data = {}

            if not isinstance(data, dict):
                data = {}

            if 200 <= response.status_code < 300:
                return data

            if should_retry_status(response.status_code) and attempt < self.max_network_retries:
                attempt += 1
                time.sleep(delay_seconds(attempt, response))
                continue

            # The same key still being processed: the first request's answer is
            # coming. Asked again with the same key, the API returns it.
            if (
                idempotency_key
                and is_idempotency_key_in_progress(response.status_code, data)
                and attempt < self.max_network_retries
            ):
                attempt += 1
                time.sleep(idempotency_conflict_delay_seconds(attempt))
                continue

            raise error_from_response(
                response.status_code,
                data,
                parse_retry_after(response),
            )
