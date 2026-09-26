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


async def _signup_verify_login(client, capture_sent_emails, email: str) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-real-password", "terms_version": "v1"},
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    await client.post("/api/v1/auth/login", json={"email": email, "password": "a-real-password"})


async def _seed_ng_stocks(db_session) -> None:
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)


async def _grant_active_subscription(db_session, email: str) -> None:
    """Creating a share link is gated behind require_feature("sharing")
    since Phase 9, per app/api/v1/share.py; these API-level tests
    predate that gate, same reasoning as tests/test_alerts.py's
    helper of the same name."""
    user_id = (
        await db_session.execute(select(users.c.id).where(users.c.email == email))
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


async def test_create_share_requires_authentication(client, db_session):
    response = await client.post("/api/v1/share")
    assert response.status_code == 401


async def test_create_share_snapshots_current_favorites(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "share-create@example.com")
    await _grant_active_subscription(db_session, "share-create@example.com")
    await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})

    response = await client.post("/api/v1/share")
    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    assert body["share_url"] == f"https://koboandcents.com/share/{body['token']}"
    assert body["expires_at"]

    # No stock_id leaked into the public payload shape, per
    # app/schemas/share.py: nothing internal in a link anyone can open.
    view = await client.get(f"/api/v1/share/{body['token']}")
    assert view.status_code == 200
    assert "stock_id" not in view.json()["items"][0]
    assert view.json()["items"][0]["ticker"] == "GTCO"


async def test_get_share_requires_no_authentication(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "share-public@example.com")
    await _grant_active_subscription(db_session, "share-public@example.com")
    await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    created = await client.post("/api/v1/share")
    token = created.json()["token"]

    await client.post("/api/v1/auth/logout")
    response = await client.get(f"/api/v1/share/{token}")
    assert response.status_code == 200
    assert response.json()["items"][0]["ticker"] == "GTCO"


async def test_get_share_404s_for_an_unknown_token(client, db_session):
    response = await client.get("/api/v1/share/not-a-real-token")
    assert response.status_code == 404


async def test_share_is_a_frozen_snapshot_not_live_data(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "share-frozen@example.com")
    await _grant_active_subscription(db_session, "share-frozen@example.com")
    added = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    stock_id = added.json()["stock_id"]

    created = await client.post("/api/v1/share")
    token = created.json()["token"]

    # Changing the favorite after the share was created should not
    # change what the already-issued link shows, per 01_product.md:
    # "here's what I'm watching right now," a snapshot, not a live view.
    await client.patch(f"/api/v1/favorites/{stock_id}", json={"status": "owned"})

    view = await client.get(f"/api/v1/share/{token}")
    assert view.json()["items"][0]["status"] == "watching"


async def test_create_share_with_no_favorites_returns_an_empty_snapshot(
    client, db_session, capture_sent_emails
):
    await _signup_verify_login(client, capture_sent_emails, "share-empty@example.com")
    await _grant_active_subscription(db_session, "share-empty@example.com")
    created = await client.post("/api/v1/share")
    assert created.status_code == 201

    view = await client.get(f"/api/v1/share/{created.json()['token']}")
    assert view.json()["items"] == []


async def test_get_share_is_rate_limited_per_ip(client, db_session):
    for _ in range(30):
        response = await client.get("/api/v1/share/probing-a-token")
        assert response.status_code == 404

    blocked = await client.get("/api/v1/share/probing-a-token")
    assert blocked.status_code == 429
