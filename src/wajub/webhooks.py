"""Webhook signature verification."""

from __future__ import annotations

import json
import time

from wajub.crypto import hmac_sha256, timing_safe_equal
from wajub.errors import WebhookSignatureVerificationError

DEFAULT_TOLERANCE_SECONDS = 300


class Webhooks:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def construct_event(
        self,
        payload: str | bytes,
        signature: str,
        timestamp: str,
        tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    ) -> dict:
        """Verify the signature and timestamp of an inbound webhook and return the decoded event.

        A tolerance of 0 or less uses the default 300s window; there is no way to disable
        replay protection.
        """
        if not self.secret:
            raise ValueError("Wajub: webhook_secret is required for webhooks.construct_event()")

        if not signature.startswith("v1="):
            raise WebhookSignatureVerificationError(
                "Invalid webhook signature format. Expected v1={hash}."
            )

        body = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        expected = hmac_sha256(self.secret, f"{timestamp}.{body}")
        received = signature[3:]

        if not timing_safe_equal(expected, received):
            raise WebhookSignatureVerificationError("Webhook signature verification failed.")

        try:
            timestamp_seconds = float(timestamp)
        except ValueError as exc:
            raise WebhookSignatureVerificationError("Invalid webhook timestamp.") from exc

        if tolerance <= 0:
            tolerance = DEFAULT_TOLERANCE_SECONDS

        drift = abs(time.time() - timestamp_seconds)
        if drift > tolerance:
            raise WebhookSignatureVerificationError(
                f"Timestamp outside tolerance zone ({int(drift)}s drift, allowed {tolerance}s)."
            )

        event = json.loads(body)
        if not isinstance(event, dict):
            raise WebhookSignatureVerificationError("Invalid webhook payload JSON.")

        return event
