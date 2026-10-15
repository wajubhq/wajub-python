"""Base HTTP client tests."""

from __future__ import annotations

import httpx
import pytest
from helpers import API_KEY, API_URL, make_client

from wajub.errors import WajubError
from wajub.http import BaseClient
from wajub.request_options import RequestOptions


def test_sends_raw_api_key_in_authorization_header() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        captured["accept"] = request.headers.get("Accept")
        return httpx.Response(200, json={"ok": True})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    client.get("/ping")

    assert captured["authorization"] == API_KEY
    assert captured["accept"] == "application/json"


def test_post_includes_idempotency_key_by_default() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idempotency"] = request.headers.get("Idempotency-Key")
        return httpx.Response(200, json={"transaction": {"id": "pay_1"}})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    client.post("/payments", {"amount": 1000})

    assert captured["idempotency"] is not None
    assert captured["idempotency"].startswith("wajub-")


def test_post_honors_custom_idempotency_key_and_sync_header() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idempotency"] = request.headers.get("Idempotency-Key")
        captured["sync"] = request.headers.get("X-Sync")
        return httpx.Response(200, json={"transaction": {"id": "pay_1"}})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    client.post(
        "/payments",
        {"amount": 1000},
        RequestOptions(idempotency_key="custom-key-123", sync="acct_sync_ref"),
    )

    assert captured["idempotency"] == "custom-key-123"
    assert captured["sync"] == "acct_sync_ref"


def test_get_does_not_send_idempotency_key() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idempotency"] = request.headers.get("Idempotency-Key")
        return httpx.Response(200, json={"transactions": []})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    client.get("/payments")

    assert captured["idempotency"] is None


def test_raises_wajub_error_on_non_success_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "Unprocessable", "code": "validation_error"})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))

    with pytest.raises(WajubError) as exc:
        client.post("/payments", {"amount": -1})

    assert exc.value.http_status == 422


def test_get_passes_query_parameters() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["query"] = str(request.url)
        return httpx.Response(200, json={"transactions": [], "meta": {}})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    client.get("/payments", {"page": 2, "status": "pending"})

    assert "page=2" in captured["query"]
    assert "status=pending" in captured["query"]
