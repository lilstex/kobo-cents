import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models.market_data import stocks
from app.models.payments import subscriptions
from app.models.portfolio import alerts
from app.models.users import users
from app.workers.tasks.refresh_market_data import refresh_market
from tests.test_refresh_market_data import _FAKE_FINANCIALS, FakeProvider, _seed_active_weights


@pytest.fixture(autouse=True)
def capture_sent_emails(monkeypatch):
    sent = []

    def fake_delay(to, subject, html):
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.api.v1.auth.send_email_task.delay", fake_delay)
    monkeypatch.setattr("app.workers.tasks.refresh_market_data.send_email_task.delay", fake_delay)
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
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "a-real-password"}
    )
    assert response.json()["status"] == "ok"


async def _seed_ng_stocks(db_session) -> None:
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)


async def _grant_active_subscription(db_session, email: str) -> None:
    """Creating an alert is gated behind require_feature("alerts")
    since Phase 9, per app/api/v1/alerts.py; these API-level tests
    predate that gate and need a real subscription row to still
    exercise the CRUD behavior they're actually testing, not the
    entitlement check itself (that's tests/test_entitlements.py's job)."""
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


async def test_alerts_requires_authentication(client, db_session):
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 401


async def test_create_score_change_alert(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-create@example.com")
    await _grant_active_subscription(db_session, "alert-create@example.com")

    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "GTCO"
    assert body["rule_type"] == "score_change"
    assert body["active"] is True


async def test_create_price_threshold_alert_validates_rule_config(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-price@example.com")
    await _grant_active_subscription(db_session, "alert-price@example.com")

    missing_direction = await client.post(
        "/api/v1/alerts",
        json={
            "ticker": "GTCO",
            "market": "NG",
            "rule_type": "price_threshold",
            "rule_config": {"price": 100},
        },
    )
    assert missing_direction.status_code == 400

    valid = await client.post(
        "/api/v1/alerts",
        json={
            "ticker": "GTCO",
            "market": "NG",
            "rule_type": "price_threshold",
            "rule_config": {"direction": "above", "price": 100},
        },
    )
    assert valid.status_code == 201


async def test_create_alert_rejects_an_unknown_rule_type(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-bad-type@example.com")
    await _grant_active_subscription(db_session, "alert-bad-type@example.com")
    response = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "vibes"}
    )
    assert response.status_code == 400


async def test_create_alert_for_unknown_ticker_404s(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "alert-unknown@example.com")
    await _grant_active_subscription(db_session, "alert-unknown@example.com")
    response = await client.post(
        "/api/v1/alerts", json={"ticker": "NOPE", "market": "NG", "rule_type": "score_change"}
    )
    assert response.status_code == 404


async def test_delete_alert(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-delete@example.com")
    await _grant_active_subscription(db_session, "alert-delete@example.com")
    created = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    alert_id = created.json()["id"]

    delete_response = await client.delete(f"/api/v1/alerts/{alert_id}")
    assert delete_response.status_code == 204

    listing = await client.get("/api/v1/alerts")
    assert listing.json()["items"] == []


async def test_delete_alert_404s_when_not_owned(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-owner-one@example.com")
    await _grant_active_subscription(db_session, "alert-owner-one@example.com")
    created = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    alert_id = created.json()["id"]

    await client.post("/api/v1/auth/logout")
    await _signup_verify_login(client, capture_sent_emails, "alert-owner-two@example.com")
    response = await client.delete(f"/api/v1/alerts/{alert_id}")
    assert response.status_code == 404


async def test_list_alerts_is_scoped_to_the_current_user(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "alert-list-one@example.com")
    await _grant_active_subscription(db_session, "alert-list-one@example.com")
    created = await client.post(
        "/api/v1/alerts", json={"ticker": "GTCO", "market": "NG", "rule_type": "score_change"}
    )
    assert created.status_code == 201

    await client.post("/api/v1/auth/logout")
    await _signup_verify_login(client, capture_sent_emails, "alert-list-two@example.com")
    listing = await client.get("/api/v1/alerts")
    assert listing.json()["items"] == []


async def test_refresh_sends_a_score_change_alert_on_a_real_bucket_transition(
    db_session, capture_sent_emails
):
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)

    # A real user row and a real alerts row, direct inserts here
    # rather than through the httpx client: this test is about the
    # refresh job's own alert-matching step, not the auth/API layer
    # already covered above.
    user_id = uuid.uuid4()
    await db_session.execute(
        users.insert().values(
            id=user_id,
            email="watcher@example.com",
            password_hash=hash_password("whatever-12345"),
            email_verified=True,
        )
    )
    gtco_id = (
        await db_session.execute(select(stocks.c.id).where(stocks.c.ticker == "GTCO"))
    ).scalar_one()
    await db_session.execute(
        alerts.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            stock_id=gtco_id,
            rule_type="score_change",
            rule_config={},
            active=True,
        )
    )

    # GTCO was the strongest of the three fake peers and landed in
    # "well"; swapping its financials for the weakest peer's numbers
    # (keeping its price) should knock it down a bucket next cycle.
    weakened_financials = dict(_FAKE_FINANCIALS)
    weakened_financials["GTCO"] = {**_FAKE_FINANCIALS["ACCESSCORP"], "price": 91.40}
    provider2 = FakeProvider(weakened_financials)
    await refresh_market("NG", provider2, db_session, cycle_id=uuid.uuid4().hex)

    matching = [e for e in capture_sent_emails if e["to"] == "watcher@example.com"]
    assert len(matching) == 1
    assert "GTCO" in matching[0]["subject"]


async def test_refresh_sends_a_price_threshold_alert_on_a_real_crossing(
    db_session, capture_sent_emails
):
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)

    user_id = uuid.uuid4()
    await db_session.execute(
        users.insert().values(
            id=user_id,
            email="price-watcher@example.com",
            password_hash=hash_password("whatever-12345"),
            email_verified=True,
        )
    )
    gtco_id = (
        await db_session.execute(select(stocks.c.id).where(stocks.c.ticker == "GTCO"))
    ).scalar_one()
    await db_session.execute(
        alerts.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            stock_id=gtco_id,
            rule_type="price_threshold",
            rule_config={"direction": "above", "price": 95.0},
            active=True,
        )
    )

    # First cycle's price (91.40) is below 95; bump it past 95 next
    # cycle, financials unchanged, isolating the price-crossing path.
    risen_financials = dict(_FAKE_FINANCIALS)
    risen_financials["GTCO"] = {**_FAKE_FINANCIALS["GTCO"], "price": 96.00}
    provider2 = FakeProvider(risen_financials)
    await refresh_market("NG", provider2, db_session, cycle_id=uuid.uuid4().hex)

    matching = [e for e in capture_sent_emails if e["to"] == "price-watcher@example.com"]
    assert len(matching) == 1
    assert "95" in matching[0]["html"] or "95.0" in matching[0]["html"]
