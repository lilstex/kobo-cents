import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.payments import subscriptions
from app.models.users import users
from app.workers.tasks.refresh_market_data import refresh_market
from tests.test_refresh_market_data import _FAKE_FINANCIALS, FakeProvider, _seed_active_weights


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


async def _signup_verify_login(client, capture_sent_emails, email: str) -> dict:
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-real-password", "terms_version": "v1"},
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    await client.post("/api/v1/auth/login", json={"email": email, "password": "a-real-password"})
    return signup.json()


async def _seed_ng_stocks(db_session) -> None:
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)


async def _get_user_id(db_session, email: str) -> uuid.UUID:
    result = await db_session.execute(select(users.c.id).where(users.c.email == email))
    return result.scalar_one()


async def test_create_alert_is_blocked_without_a_subscription(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "no-sub@example.com")
    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 402


async def test_create_share_is_blocked_without_a_subscription(
    client, db_session, capture_sent_emails
):
    await _signup_verify_login(client, capture_sent_emails, "no-sub-share@example.com")
    response = await client.post("/api/v1/share")
    assert response.status_code == 402


async def test_create_alert_succeeds_with_an_active_subscription(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "active-sub@example.com")
    user_id = await _get_user_id(db_session, "active-sub@example.com")
    await db_session.execute(
        subscriptions.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="paystack",
            provider_subscription_id="kc_test",
            status="active",
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )
    )

    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 201


async def test_create_alert_is_blocked_with_an_expired_subscription(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "expired-sub@example.com")
    user_id = await _get_user_id(db_session, "expired-sub@example.com")
    await db_session.execute(
        subscriptions.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="paystack",
            provider_subscription_id="kc_test",
            status="active",
            current_period_end=datetime.now(UTC) - timedelta(days=1),
        )
    )

    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 402


async def test_create_alert_succeeds_via_a_posthog_feature_flag_override(
    client, db_session, capture_sent_emails, monkeypatch
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "flag-override@example.com")
    monkeypatch.setattr(
        "app.services.entitlements.feature_flag_enabled", lambda flag, user_id: True
    )

    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 201


async def test_deleting_and_listing_alerts_still_works_without_a_subscription(
    client, db_session, capture_sent_emails
):
    """Only creating a new alert is gated, per app/api/v1/alerts.py's
    own reasoning: a lapsed subscriber keeps visibility and cleanup
    rights over what they already created."""
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "manage-without-sub@example.com")
    user_id = await _get_user_id(db_session, "manage-without-sub@example.com")
    await db_session.execute(
        subscriptions.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            provider="paystack",
            provider_subscription_id="kc_test",
            status="active",
            current_period_end=datetime.now(UTC) + timedelta(days=30),
        )
    )
    created = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    alert_id = created.json()["id"]

    # Subscription lapses.
    await db_session.execute(
        subscriptions.update()
        .where(subscriptions.c.user_id == user_id)
        .values(current_period_end=datetime.now(UTC) - timedelta(days=1))
    )

    listing = await client.get("/api/v1/alerts")
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1

    delete_response = await client.delete(f"/api/v1/alerts/{alert_id}")
    assert delete_response.status_code == 204
