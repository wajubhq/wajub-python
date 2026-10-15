"""Wajub client tests."""

from __future__ import annotations

import pytest
from helpers import API_KEY

from wajub import Wajub


def test_requires_api_key() -> None:
    with pytest.raises(ValueError, match="api_key is required"):
        Wajub(api_key="")


def test_reads_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAJUB_API_KEY", API_KEY)
    wajub = Wajub()
    assert wajub.payments.api_key == API_KEY


def test_exposes_all_resources() -> None:
    wajub = Wajub(api_key=API_KEY)

    assert wajub.global_ is not None
    assert wajub.payments is not None
    assert wajub.customers is not None
    assert wajub.refunds is not None
    assert wajub.transfers is not None
    assert wajub.beneficiaries is not None
    assert wajub.links is not None
    assert wajub.balance is not None
    assert wajub.events is not None
    assert wajub.accounts is not None
    assert wajub.webhook_endpoints is not None
    assert wajub.invoices is not None
    assert wajub.disputes is not None
    assert wajub.identity is not None
    assert wajub.tax is not None
    assert wajub.shield is not None
    assert wajub.listen is not None
    assert wajub.webhooks is not None


def test_accepts_public_and_restricted_keys() -> None:
    assert Wajub(api_key="pk_test.public") is not None
    assert Wajub(api_key="rk_test.restricted") is not None


def test_webhook_secret_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAJUB_API_KEY", API_KEY)
    monkeypatch.setenv("WAJUB_WEBHOOK_SECRET", "whsec_test")
    wajub = Wajub()
    assert wajub.webhooks.secret == "whsec_test"


def test_global_alias_via_getattr() -> None:
    wajub = Wajub(api_key=API_KEY)
    assert getattr(wajub, "global") is wajub.global_


def test_context_manager_closes_http_client() -> None:
    with Wajub(api_key=API_KEY) as wajub:
        assert wajub.payments is not None
