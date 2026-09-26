import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.payments import subscriptions
from app.models.users import users


@pytest.fixture(autouse=True)
def capture_sent_emails(monkeypatch):
    sent = []

    def fake_delay(to, subject, html):
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.api.v1.auth.send_email_task.delay", fake_delay)
    return sent


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


async def test_entitlement_requires_authentication(client, db_session):
    response = await client.get("/api/v1/subscriptions/entitlement", params={"feature": "alerts"})
    assert response.status_code == 401


async def test_entitlement_is_false_without_a_subscription(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "ent-none@example.com")
    response = await client.get("/api/v1/subscriptions/entitlement", params={"feature": "alerts"})
    assert response.status_code == 200
    assert response.json()["entitled"] is False


async def test_entitlement_is_true_with_an_active_subscription(
    client, db_session, capture_sent_emails
):
    await _signup_verify_login(client, capture_sent_emails, "ent-active@example.com")
    user_id = (
        await db_session.execute(
            select(users.c.id).where(users.c.email == "ent-active@example.com")
        )
    ).scalar_one()
    await db_session.execute(
        subscriptions.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="paystack",
            provider_subscription_id="test-sub",
            status="active",
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )
    )

    response = await client.get("/api/v1/subscriptions/entitlement", params={"feature": "alerts"})
    assert response.json()["entitled"] is True

    # sharing is a different feature: this subscription genuinely
    # entitles the user to every paid feature, not just the one asked
    # about in the same request, since it's one flat paid tier per
    # docs/01_product.md's monetization section, not per-feature plans.
    sharing = await client.get("/api/v1/subscriptions/entitlement", params={"feature": "sharing"})
    assert sharing.json()["entitled"] is True


async def test_entitlement_via_a_posthog_feature_flag_override(
    client, db_session, capture_sent_emails, monkeypatch
):
    await _signup_verify_login(client, capture_sent_emails, "ent-flag@example.com")
    monkeypatch.setattr(
        "app.services.entitlements.feature_flag_enabled", lambda flag, user_id: True
    )
    response = await client.get("/api/v1/subscriptions/entitlement", params={"feature": "alerts"})
    assert response.json()["entitled"] is True
