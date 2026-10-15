"""An API key that cannot be sent is refused, and never shown in an error."""

from __future__ import annotations

import httpx
import pytest
from helpers import API_URL, make_client

from wajub import Wajub
from wajub.http import BaseClient

SECRET = "sk_test.s3cr3tPart"
UNSENDABLE = [
    f"{SECRET}\ninjected",
    f"{SECRET}\r\nX-Other: 1",
    f"{SECRET}é",
    f"{SECRET} {SECRET}",
    f"{SECRET}\x00",
    f"{SECRET}\t1",
]


def _never_called(request: httpx.Request) -> httpx.Response:
    raise AssertionError("no request should be sent")


@pytest.mark.parametrize("key", UNSENDABLE)
def test_the_client_refuses_an_unsendable_key_without_showing_it(key: str) -> None:
    http = make_client(httpx.MockTransport(_never_called))

    with pytest.raises(ValueError, match="API key") as raised:
        Wajub(api_key=key, http_client=http)

    assert "s3cr3tPart" not in str(raised.value)
    assert "s3cr3tPart" not in repr(raised.value)


@pytest.mark.parametrize("key", UNSENDABLE)
def test_a_resource_refuses_an_unsendable_key_before_sending(key: str) -> None:
    client = BaseClient(key, API_URL, client=make_client(httpx.MockTransport(_never_called)))

    for call in (lambda: client.get("/balance"), lambda: client.post("/payments", {"a": 1})):
        with pytest.raises(ValueError, match="API key") as raised:
            call()
        assert "s3cr3tPart" not in str(raised.value)
        assert raised.value.__cause__ is None and raised.value.__context__ is None


@pytest.mark.parametrize("key", [SECRET, f"  {SECRET}\n", f"Bearer {SECRET}", f"bearer  {SECRET}"])
def test_a_key_with_only_surrounding_space_or_a_bearer_prefix_is_sent(key: str) -> None:
    sent: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.headers["Authorization"])
        return httpx.Response(200, json={})

    with Wajub(api_key=key, http_client=make_client(httpx.MockTransport(handler))) as wajub:
        wajub.balance.retrieve()

    assert sent == [SECRET]
