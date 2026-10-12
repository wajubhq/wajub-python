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


IN_PROGRESS = {
    "code": 409,
    "status": "Conflict",
    "message": "A request with this Idempotency-Key is still being processed.",
    "errors": {
        "idempotency_key": ["A request with this Idempotency-Key is still being processed."]
    },
}


def test_asks_again_with_the_same_key_while_it_is_still_being_processed(monkeypatch) -> None:
    # A call sent again after a timeout can reach the API while the first one
    # is still running: the answer is on its way, so the client asks again.
    sleeps: list[float] = []
    monkeypatch.setattr("wajub.http.time.sleep", sleeps.append)
    keys: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        keys.append(request.headers.get("Idempotency-Key"))
        if len(keys) == 1:
            return httpx.Response(409, json=IN_PROGRESS)
        return httpx.Response(201, json={"transaction": {"id": "trx_1"}})

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))
    result = client.post("/payments", {"amount": 1000})

    assert result["transaction"]["id"] == "trx_1"
    assert len(keys) == 2 and keys[0] == keys[1]
    assert sleeps == [2.0]


def test_raises_any_other_409_at_once(monkeypatch) -> None:
    monkeypatch.setattr("wajub.http.time.sleep", lambda _s: None)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            409,
            json={
                "code": 409,
                "error_code": "payment_in_progress",
                "message": "A charge is already in progress.",
            },
        )

    client = BaseClient(API_KEY, API_URL, client=make_client(httpx.MockTransport(handler)))

    try:
        client.post("/payments/trx_1", {"channel": "cm.mtn"})
    except Exception as exc:  # noqa: BLE001
        assert "already in progress" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected an error")
    assert calls["n"] == 1


def test_waits_2_then_4_then_8_seconds_for_a_key_in_progress() -> None:
    from wajub.retry import idempotency_conflict_delay_seconds

    assert [idempotency_conflict_delay_seconds(a) for a in (1, 2, 3)] == [2.0, 4.0, 8.0]
