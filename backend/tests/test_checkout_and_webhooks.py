import hashlib
import hmac
import json
import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.redis import redis_client
from app.models.payments import subscriptions
from app.models.users import users
from app.workers.tasks.subscription_tasks import activate_subscription


@pytest.fixture(autouse=True)
def capture_sent_emails(monkeypatch):
    sent = []

    def fake_delay(to, subject, html):
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.api.v1.auth.send_email_task.delay", fake_delay)
    return sent


@pytest.fixture(autouse=True)
def capture_subscription_activations(monkeypatch, db_session):
    """activate_subscription_task.delay() is fire-and-forget against a
    real Celery worker, which isn't running in tests; this captures
    the coroutine instead so a test can await it explicitly, using the
    test's own rolled-back-transaction db_session rather than the
    task's normal async_session_factory(), the same boundary-crossing
    pattern already established for send_email_task.delay above."""
    pending = []

    def fake_delay(user_id, provider_name, reference):
        pending.append(
            activate_subscription(db_session, uuid.UUID(user_id), provider_name, reference)
        )

    monkeypatch.setattr("app.api.v1.webhooks.activate_subscription_task.delay", fake_delay)
    return pending


async def _run_pending_activations(pending: list) -> None:
    for coro in pending:
        await coro
    pending.clear()


def _extract_token(html: str) -> str:
    match = re.search(r"token=([^\"&]+)", html)
    assert match, f"no token found in: {html}"
    return match.group(1)


async def _signup_verify_login(client, capture_sent_emails, email: str) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-real-password", "terms_version": "v1"},
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    await client.post("/api/v1/auth/login", json={"email": email, "password": "a-real-password"})


async def _get_user_id(db_session, email: str) -> uuid.UUID:
    result = await db_session.execute(select(users.c.id).where(users.c.email == email))
    return result.scalar_one()


async def test_checkout_503s_without_a_configured_provider(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "checkout-unconfigured@example.com")
    response = await client.post("/api/v1/subscriptions/checkout", json={"provider": "paystack"})
    assert response.status_code == 503


async def test_checkout_rejects_an_unknown_provider(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "checkout-bad-provider@example.com")
    response = await client.post("/api/v1/subscriptions/checkout", json={"provider": "stripe"})
    assert response.status_code == 400


async def test_checkout_creates_a_redis_mapping_for_the_reference(
    client, db_session, capture_sent_emails, monkeypatch
):
    monkeypatch.setattr(
        "app.integrations.payments.paystack.settings.paystack_secret_key", "sk_test_123"
    )
    await _signup_verify_login(client, capture_sent_emails, "checkout-ok@example.com")

    captured_request_body = {}
    original_post = httpx.AsyncClient.post

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        # The test client (`client` fixture) is also an httpx.AsyncClient,
        # calling this same patched method for every request it makes
        # to the app under test; only the real Paystack URL should be
        # faked, anything else (the app's own ASGI-transport calls)
        # has to fall through to the real implementation.
        if "paystack.co" not in str(url):
            return await original_post(self, url, headers=headers, json=json, **kwargs)
        captured_request_body.update(json)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "data": {
                    "authorization_url": "https://checkout.paystack.com/abc",
                    "reference": json["reference"],
                }
            },
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await client.post("/api/v1/subscriptions/checkout", json={"provider": "paystack"})
    assert response.status_code == 201
    assert response.json()["redirect_url"] == "https://checkout.paystack.com/abc"

    # The exact reference sent to the provider is what the webhook
    # handler will look up later, per app/api/v1/subscriptions.py.
    reference = captured_request_body["reference"]
    stored = await redis_client.get(f"checkout:{reference}")
    assert stored is not None
    assert json.loads(stored)["provider"] == "paystack"


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()


async def test_paystack_webhook_rejects_an_invalid_signature(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.paystack.settings.paystack_secret_key", "sk_real"
    )
    response = await client.post(
        "/api/v1/webhooks/paystack",
        content=b'{"event":"charge.success","data":{"id":1,"reference":"ref-x"}}',
        headers={"x-paystack-signature": "forged"},
    )
    assert response.status_code == 401


async def test_paystack_webhook_with_no_matching_checkout_is_acknowledged_but_creates_nothing(
    client, db_session, monkeypatch
):
    secret = "sk_real"
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", secret)
    body = json.dumps(
        {"event": "charge.success", "data": {"id": 1, "reference": "no-such-ref"}}
    ).encode()
    response = await client.post(
        "/api/v1/webhooks/paystack",
        content=body,
        headers={"x-paystack-signature": _sign(secret, body)},
    )
    assert response.status_code == 200
    count = (await db_session.execute(select(subscriptions.c.id))).all()
    assert count == []


async def test_paystack_webhook_activates_a_subscription_for_the_checkout_user(
    client, db_session, capture_sent_emails, capture_subscription_activations, monkeypatch
):
    secret = "sk_real"
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", secret)
    await _signup_verify_login(client, capture_sent_emails, "webhook-activate@example.com")
    user_id = await _get_user_id(db_session, "webhook-activate@example.com")

    reference = "kc_real_checkout"
    await redis_client.set(
        f"checkout:{reference}",
        json.dumps({"user_id": str(user_id), "provider": "paystack"}),
        ex=3600,
    )

    body = json.dumps(
        {"event": "charge.success", "data": {"id": 555, "reference": reference}}
    ).encode()
    response = await client.post(
        "/api/v1/webhooks/paystack",
        content=body,
        headers={"x-paystack-signature": _sign(secret, body)},
    )
    assert response.status_code == 200
    await _run_pending_activations(capture_subscription_activations)

    sub = (
        (await db_session.execute(select(subscriptions).where(subscriptions.c.user_id == user_id)))
        .mappings()
        .first()
    )
    assert sub is not None
    assert sub["status"] == "active"
    assert sub["current_period_end"] > datetime.now(UTC) + timedelta(days=29)


async def test_a_redelivered_webhook_event_does_not_double_extend_the_period(
    client, db_session, capture_sent_emails, capture_subscription_activations, monkeypatch
):
    secret = "sk_real"
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", secret)
    await _signup_verify_login(client, capture_sent_emails, "webhook-redelivered@example.com")
    user_id = await _get_user_id(db_session, "webhook-redelivered@example.com")

    reference = "kc_redelivered"
    await redis_client.set(
        f"checkout:{reference}",
        json.dumps({"user_id": str(user_id), "provider": "paystack"}),
        ex=3600,
    )
    body = json.dumps(
        {"event": "charge.success", "data": {"id": 777, "reference": reference}}
    ).encode()
    headers = {"x-paystack-signature": _sign(secret, body)}

    first = await client.post("/api/v1/webhooks/paystack", content=body, headers=headers)
    assert first.status_code == 200
    # The unique constraint only guards against a second insert into
    # payment_events; nothing stops a second activation dispatch
    # unless the route itself returns early first, which is exactly
    # the behavior this test verifies, so run whatever the first call
    # actually queued before reading the resulting period.
    await _run_pending_activations(capture_subscription_activations)
    first_period_end = (
        await db_session.execute(
            select(subscriptions.c.current_period_end).where(subscriptions.c.user_id == user_id)
        )
    ).scalar_one()

    # Same event id redelivered: the unique constraint on
    # (provider, provider_event_id) catches it, per 02.md, before any
    # further processing, the period should not move again.
    second = await client.post("/api/v1/webhooks/paystack", content=body, headers=headers)
    assert second.status_code == 200
    assert capture_subscription_activations == []
    second_period_end = (
        await db_session.execute(
            select(subscriptions.c.current_period_end).where(subscriptions.c.user_id == user_id)
        )
    ).scalar_one()
    assert second_period_end == first_period_end


async def test_a_new_successful_charge_extends_an_existing_active_subscription(
    client, db_session, capture_sent_emails, capture_subscription_activations, monkeypatch
):
    secret = "sk_real"
    monkeypatch.setattr("app.integrations.payments.paystack.settings.paystack_secret_key", secret)
    await _signup_verify_login(client, capture_sent_emails, "webhook-extend@example.com")
    user_id = await _get_user_id(db_session, "webhook-extend@example.com")

    original_end = datetime.now(UTC) + timedelta(days=10)
    await db_session.execute(
        subscriptions.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="paystack",
            provider_subscription_id="kc_original",
            status="active",
            current_period_end=original_end,
        )
    )

    reference = "kc_renewal"
    await redis_client.set(
        f"checkout:{reference}",
        json.dumps({"user_id": str(user_id), "provider": "paystack"}),
        ex=3600,
    )
    body = json.dumps(
        {"event": "charge.success", "data": {"id": 888, "reference": reference}}
    ).encode()
    response = await client.post(
        "/api/v1/webhooks/paystack",
        content=body,
        headers={"x-paystack-signature": _sign(secret, body)},
    )
    assert response.status_code == 200
    await _run_pending_activations(capture_subscription_activations)

    new_end = (
        await db_session.execute(
            select(subscriptions.c.current_period_end).where(subscriptions.c.user_id == user_id)
        )
    ).scalar_one()
    assert new_end > original_end


async def test_flutterwave_checkout_creates_a_redis_mapping_for_the_reference(
    client, db_session, capture_sent_emails, monkeypatch
):
    """Phase 11's "integration tests for every endpoint" applies to
    Flutterwave's checkout path exactly as much as Paystack's: both
    are named in docs/backend-architecture/00.md for real redundancy
    reasons, not one primary and one decorative option, and every
    other test in this file only ever exercised Paystack."""
    monkeypatch.setattr(
        "app.integrations.payments.flutterwave.settings.flutterwave_secret_key", "fw_test_123"
    )
    await _signup_verify_login(client, capture_sent_emails, "checkout-fw-ok@example.com")

    captured_request_body = {}
    original_post = httpx.AsyncClient.post

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        if "flutterwave.com" not in str(url):
            return await original_post(self, url, headers=headers, json=json, **kwargs)
        captured_request_body.update(json)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"data": {"link": "https://checkout.flutterwave.com/xyz"}},
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await client.post("/api/v1/subscriptions/checkout", json={"provider": "flutterwave"})
    assert response.status_code == 201
    assert response.json()["redirect_url"] == "https://checkout.flutterwave.com/xyz"

    reference = captured_request_body["tx_ref"]
    stored = await redis_client.get(f"checkout:{reference}")
    assert stored is not None
    assert json.loads(stored)["provider"] == "flutterwave"


async def test_flutterwave_webhook_rejects_an_invalid_signature(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "app.integrations.payments.flutterwave.settings.flutterwave_webhook_secret_hash",
        "the-real-hash",
    )
    response = await client.post(
        "/api/v1/webhooks/flutterwave",
        content=b'{"event":"charge.completed","data":{"id":1,"tx_ref":"ref-x","status":"successful"}}',
        headers={"verif-hash": "forged"},
    )
    assert response.status_code == 401


async def test_flutterwave_webhook_activates_a_subscription_for_the_checkout_user(
    client, db_session, capture_sent_emails, capture_subscription_activations, monkeypatch
):
    secret_hash = "the-real-hash"
    monkeypatch.setattr(
        "app.integrations.payments.flutterwave.settings.flutterwave_webhook_secret_hash",
        secret_hash,
    )
    await _signup_verify_login(client, capture_sent_emails, "webhook-fw-activate@example.com")
    user_id = await _get_user_id(db_session, "webhook-fw-activate@example.com")

    reference = "kc_fw_checkout"
    await redis_client.set(
        f"checkout:{reference}",
        json.dumps({"user_id": str(user_id), "provider": "flutterwave"}),
        ex=3600,
    )
    body = json.dumps(
        {
            "event": "charge.completed",
            "data": {"id": 999, "tx_ref": reference, "status": "successful"},
        }
    ).encode()
    response = await client.post(
        "/api/v1/webhooks/flutterwave",
        content=body,
        headers={"verif-hash": secret_hash},
    )
    assert response.status_code == 200
    await _run_pending_activations(capture_subscription_activations)

    sub = (
        (
            await db_session.execute(
                select(subscriptions).where(
                    subscriptions.c.user_id == user_id, subscriptions.c.provider == "flutterwave"
                )
            )
        )
        .mappings()
        .first()
    )
    assert sub is not None
    assert sub["status"] == "active"
    assert sub["current_period_end"] > datetime.now(UTC) + timedelta(days=29)
