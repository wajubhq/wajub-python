"""Shared test helpers."""

from __future__ import annotations

import httpx

from wajub.http_utils import API_URL

API_KEY = "sk_test.unit_test_key"


def make_client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(base_url=API_URL, transport=handler)
