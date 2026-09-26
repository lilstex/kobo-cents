import hashlib
import hmac

import httpx
import pytest

from app.integrations.payments.base import ProviderNotConfiguredError
from app.integrations.payments.flutterwave import FlutterwaveAdapter
from app.integrations.payments.paystack import PaystackAdapter


async def test_paystack_raises_without_a_configured_secret_key(monkeypatch):
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", "")
    with pytest.raises(ProviderNotConfiguredError):
        await PaystackAdapter().create_checkout(
            email="a@example.com",
            reference="ref-1",
            amount=2500,
            currency="NGN",
            callback_url="https://example.com",
        )


async def test_paystack_create_checkout_maps_a_realistic_response(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.paystack.settings.paystack_secret_key", "sk_test_123"
    )

    captured = {}

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        captured["url"] = url
        captured["json"] = json
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "data": {
                    "authorization_url": "https://checkout.paystack.com/abc123",
                    "reference": "ref-1",
                }
            },
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    session = await PaystackAdapter().create_checkout(
        email="a@example.com",
        reference="ref-1",
        amount=2500,
        currency="NGN",
        callback_url="https://example.com/callback",
    )

    assert session.redirect_url == "https://checkout.paystack.com/abc123"
    assert session.reference == "ref-1"
    # Paystack takes kobo, not naira: 100x the given amount.
    assert captured["json"]["amount"] == 250_000


def test_paystack_verify_webhook_signature_accepts_a_valid_hmac(monkeypatch):
    secret = "sk_test_123"
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", secret)
    body = b'{"event":"charge.success"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    adapter = PaystackAdapter()
    assert adapter.verify_webhook_signature(body, {"x-paystack-signature": signature}) is True


def test_paystack_verify_webhook_signature_rejects_a_forged_signature(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.paystack.settings.paystack_secret_key", "sk_real"
    )
    adapter = PaystackAdapter()
    body = b'{"event":"charge.success"}'
    assert (
        adapter.verify_webhook_signature(body, {"x-paystack-signature": "not-the-real-one"})
        is False
    )


def test_paystack_parse_webhook_event_recognizes_a_successful_charge():
    payload = {"event": "charge.success", "data": {"id": 12345, "reference": "ref-1"}}
    event = PaystackAdapter().parse_webhook_event(payload)
    assert event.status == "successful"
    assert event.event_id == "12345"
    assert event.reference == "ref-1"


def test_paystack_parse_webhook_event_treats_other_events_as_not_successful():
    payload = {"event": "charge.failed", "data": {"id": 1, "reference": "ref-1"}}
    event = PaystackAdapter().parse_webhook_event(payload)
    assert event.status == "other"


async def test_flutterwave_raises_without_a_configured_secret_key(monkeypatch):
    monkeypatch.setattr("app.integrations.payments.flutterwave.settings.flutterwave_secret_key", "")
    with pytest.raises(ProviderNotConfiguredError):
        await FlutterwaveAdapter().create_checkout(
            email="a@example.com",
            reference="ref-1",
            amount=5,
            currency="USD",
            callback_url="https://example.com",
        )


async def test_flutterwave_create_checkout_maps_a_realistic_response(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.flutterwave.settings.flutterwave_secret_key", "fw_test_123"
    )

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200, json={"data": {"link": "https://checkout.flutterwave.com/xyz"}}, request=request
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    session = await FlutterwaveAdapter().create_checkout(
        email="a@example.com",
        reference="ref-2",
        amount=5,
        currency="USD",
        callback_url="https://example.com/callback",
    )
    assert session.redirect_url == "https://checkout.flutterwave.com/xyz"
    assert session.reference == "ref-2"


def test_flutterwave_verify_webhook_signature_is_a_direct_comparison(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.flutterwave.settings.flutterwave_webhook_secret_hash",
        "the-real-hash",
    )
    adapter = FlutterwaveAdapter()
    assert adapter.verify_webhook_signature(b"", {"verif-hash": "the-real-hash"}) is True
    assert adapter.verify_webhook_signature(b"", {"verif-hash": "wrong"}) is False


def test_flutterwave_parse_webhook_event_recognizes_a_successful_charge():
    payload = {
        "event": "charge.completed",
        "data": {"id": 99, "tx_ref": "ref-2", "status": "successful"},
    }
    event = FlutterwaveAdapter().parse_webhook_event(payload)
    assert event.status == "successful"
    assert event.event_id == "99"
    assert event.reference == "ref-2"
