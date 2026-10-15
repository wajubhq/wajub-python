"""Webhook verification tests."""

from __future__ import annotations

import time

import pytest

from wajub.crypto import hmac_sha256
from wajub.errors import WebhookSignatureVerificationError
from wajub.webhooks import Webhooks

SECRET = "whsec_test_abc123"


def sign(payload: str, timestamp: int) -> str:
    return "v1=" + hmac_sha256(SECRET, f"{timestamp}.{payload}")


def test_construct_event_parses_valid_payload() -> None:
    payload = '{"event":"payment.succeeded","data":{"id":"trx_1"}}'
    ts = int(time.time())
    event = Webhooks(SECRET).construct_event(payload, sign(payload, ts), str(ts))
    assert event["event"] == "payment.succeeded"
    assert event["data"]["id"] == "trx_1"


def test_construct_event_rejects_invalid_signature_format() -> None:
    with pytest.raises(WebhookSignatureVerificationError):
        Webhooks(SECRET).construct_event("{}", "bad-format", str(int(time.time())))


def test_construct_event_rejects_wrong_signature() -> None:
    payload = '{"event":"payment.succeeded"}'
    with pytest.raises(WebhookSignatureVerificationError):
        Webhooks(SECRET).construct_event(payload, "v1=deadbeef", str(int(time.time())))


def test_construct_event_rejects_timestamp_outside_tolerance() -> None:
    payload = '{"event":"payment.succeeded"}'
    old_ts = int(time.time()) - 600
    with pytest.raises(WebhookSignatureVerificationError):
        Webhooks(SECRET).construct_event(payload, sign(payload, old_ts), str(old_ts), 300)


def test_construct_event_requires_webhook_secret() -> None:
    with pytest.raises(ValueError, match="webhook_secret"):
        Webhooks("").construct_event("{}", "v1=abc", str(int(time.time())))


@pytest.mark.parametrize(
    ("signature", "timestamp"),
    [(None, "1760000000"), ("v1=deadbeef", None), ("", "1760000000")],
)
def test_construct_event_answers_a_missing_header_with_a_signature_error(
    signature, timestamp
) -> None:
    with pytest.raises(WebhookSignatureVerificationError, match="Missing X-Wajub-Signature"):
        Webhooks(SECRET).construct_event('{"event":"payment.succeeded"}', signature, timestamp)
