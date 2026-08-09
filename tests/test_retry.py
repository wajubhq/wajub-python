"""HTTP retry behavior tests."""

from __future__ import annotations

import httpx

from wajub.http import BaseClient
from wajub.http_utils import API_URL
from helpers import API_KEY, make_client


def test_retries_on_503_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"message": "Unavailable"})
        return httpx.Response(200, json={"ok": True})

    client = BaseClient(
        API_KEY, API_URL, client=make_client(httpx.MockTransport(handler))
    )
    result = client.get("/ping")

    assert result["ok"] is True
    assert calls["n"] == 2
