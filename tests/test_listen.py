"""listen.config() and listen.auth() are deprecated: the API retired them."""

from __future__ import annotations

import httpx
import pytest
from helpers import API_KEY, API_URL, make_client

from wajub.resources import ListenResource


def _listen(captured: list[httpx.Request]) -> ListenResource:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"config": {"ok": True}, "auth": {"ok": True}})

    return ListenResource(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


def test_config_warns_and_still_sends_the_request() -> None:
    captured: list[httpx.Request] = []

    with pytest.warns(DeprecationWarning, match="wajub listen") as record:
        result = _listen(captured).config()

    assert record[0].filename == __file__
    assert result == {"ok": True}
    assert [(r.method, r.url.path) for r in captured] == [("GET", "/listen/config")]


def test_auth_warns_and_still_sends_the_request() -> None:
    captured: list[httpx.Request] = []

    with pytest.warns(DeprecationWarning, match="wajub listen") as record:
        result = _listen(captured).auth({"device": "laptop"})

    assert record[0].filename == __file__
    assert result == {"ok": True}
    assert [(r.method, r.url.path) for r in captured] == [("POST", "/listen/auth")]
