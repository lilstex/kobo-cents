import re
import uuid

import pytest

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


async def test_price_history_requires_authentication(client, db_session):
    response = await client.get("/api/v1/stocks/GTCO/price-history")
    assert response.status_code == 401


async def test_price_history_returns_points_oldest_first(client, db_session, capture_sent_emails):
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)

    risen = dict(_FAKE_FINANCIALS)
    risen["GTCO"] = {**_FAKE_FINANCIALS["GTCO"], "price": 95.00}
    await refresh_market("NG", FakeProvider(risen), db_session, cycle_id=uuid.uuid4().hex)

    await _signup_verify_login(client, capture_sent_emails, "price-history@example.com")
    response = await client.get("/api/v1/stocks/GTCO/price-history")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["price"] for item in items] == [91.4, 95.0]


async def test_price_history_404s_for_an_unknown_ticker(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "price-history-404@example.com")
    response = await client.get("/api/v1/stocks/NOPE/price-history")
    assert response.status_code == 404
