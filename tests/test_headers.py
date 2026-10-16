"""A header given in RequestOptions goes out once, whatever the case of its name."""

from __future__ import annotations

import httpx
import pytest
from helpers import API_KEY, API_URL, make_client

from wajub.http import BaseClient
from wajub.request_options import RequestOptions


def _client(captured: list[httpx.Request]) -> BaseClient:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={})

    return BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))


@pytest.mark.parametrize("name", ["Authorization", "authorization", "AUTHORIZATION"])
def test_an_authorization_header_replaces_the_clients_key_for_that_request(name: str) -> None:
    captured: list[httpx.Request] = []
    client = _client(captured)

    client.post("/payments", {"a": 1}, RequestOptions(headers={name: "Bearer sk_test.other"}))
    client.post("/payments", {"a": 1})

    assert captured[0].headers.get_list("Authorization") == ["sk_test.other"]
    assert captured[1].headers.get_list("Authorization") == [API_KEY]


def test_an_unsendable_authorization_header_is_refused_without_showing_it() -> None:
    captured: list[httpx.Request] = []

    with pytest.raises(ValueError, match="API key") as raised:
        _client(captured).post(
            "/payments", {"a": 1}, RequestOptions(headers={"authorization": "sk_test.s3cr3t\nX"})
        )

    assert "s3cr3t" not in str(raised.value)
    assert captured == []


@pytest.mark.parametrize("name", ["X-Sync", "x-sync", "X-SYNC"])
def test_an_x_sync_header_counts_as_the_sync_option(name: str) -> None:
    captured: list[httpx.Request] = []
    client = _client(captured)

    client.post("/payments", {"a": 1}, RequestOptions(headers={name: "acct_1"}))
    client.post("/payments", {"a": 1}, RequestOptions(sync="acct_1", headers={name: "acct_1"}))
    client.post("/payments", {"a": 1}, RequestOptions(sync=" ", headers={name: "acct_1"}))
    client.post("/payments", {"a": 1}, RequestOptions(sync="acct_1", headers={name: ""}))

    assert [r.headers.get_list("X-Sync") for r in captured] == [["acct_1"]] * 4


def test_an_x_sync_header_that_differs_from_the_sync_option_is_refused() -> None:
    captured: list[httpx.Request] = []

    with pytest.raises(ValueError, match="X-Sync"):
        _client(captured).post(
            "/payments", {"a": 1}, RequestOptions(sync="acct_1", headers={"x-sync": "acct_2"})
        )
    with pytest.raises(ValueError, match="X-Sync"):
        _client(captured).post(
            "/payments",
            {"a": 1},
            RequestOptions(headers={"X-Sync": "acct_1", "x-sync": "acct_2"}),
        )

    assert captured == []


def test_accept_and_content_type_go_out_once() -> None:
    captured: list[httpx.Request] = []

    _client(captured).post(
        "/payments",
        {"a": 1},
        RequestOptions(
            headers={"accept": "application/problem+json", "content-type": "text/plain"}
        ),
    )

    assert captured[0].headers.get_list("Accept") == ["application/problem+json"]
    assert captured[0].headers.get_list("Content-Type") == ["application/json"]
