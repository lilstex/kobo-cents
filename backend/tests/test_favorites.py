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
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "a-real-password"}
    )
    assert response.json()["status"] == "ok"


async def _seed_ng_stocks(db_session) -> None:
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)


async def test_favorites_requires_authentication(client, db_session):
    await _seed_ng_stocks(db_session)
    response = await client.get("/api/v1/favorites")
    assert response.status_code == 401


async def test_add_favorite_defaults_to_watching(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "add-fav@example.com")

    response = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "GTCO"
    assert body["status"] == "watching"
    assert body["composite_score"] is not None


async def test_add_favorite_is_idempotent_and_keeps_existing_status(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "idempotent-fav@example.com")

    first = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    stock_id = first.json()["stock_id"]
    await client.patch(f"/api/v1/favorites/{stock_id}", json={"status": "owned"})

    second = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    assert second.status_code == 201
    # Re-adding an already-favorited stock doesn't reset it back to
    # "watching", the insert is a no-op on conflict, per the real
    # user expectation of clicking an already-active favorite button.
    assert second.json()["status"] == "owned"

    listing = await client.get("/api/v1/favorites")
    assert len(listing.json()["items"]) == 1


async def test_add_favorite_for_unknown_ticker_404s(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "unknown-fav@example.com")
    response = await client.post("/api/v1/favorites", json={"ticker": "NOPE", "market": "NG"})
    assert response.status_code == 404


async def test_update_favorite_status_switches_to_owned(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "switch-fav@example.com")
    added = await client.post("/api/v1/favorites", json={"ticker": "ZENITHBANK", "market": "NG"})
    stock_id = added.json()["stock_id"]

    response = await client.patch(f"/api/v1/favorites/{stock_id}", json={"status": "owned"})
    assert response.status_code == 200
    assert response.json()["status"] == "owned"


async def test_update_favorite_status_rejects_an_unknown_status(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "bad-status-fav@example.com")
    added = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    stock_id = added.json()["stock_id"]

    response = await client.patch(f"/api/v1/favorites/{stock_id}", json={"status": "bought"})
    assert response.status_code == 400


async def test_update_favorite_status_404s_for_something_never_favorited(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "never-fav@example.com")
    random_stock_id = uuid.uuid4()
    response = await client.patch(f"/api/v1/favorites/{random_stock_id}", json={"status": "owned"})
    assert response.status_code == 404


async def test_remove_favorite_deletes_it(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "remove-fav@example.com")
    added = await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})
    stock_id = added.json()["stock_id"]

    delete_response = await client.delete(f"/api/v1/favorites/{stock_id}")
    assert delete_response.status_code == 204

    listing = await client.get("/api/v1/favorites")
    assert listing.json()["items"] == []


async def test_remove_favorite_404s_when_not_favorited(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "remove-missing-fav@example.com")
    response = await client.delete(f"/api/v1/favorites/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_list_favorites_is_scoped_to_the_current_user(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "user-one@example.com")
    await client.post("/api/v1/favorites", json={"ticker": "GTCO", "market": "NG"})

    await client.post("/api/v1/auth/logout")
    await _signup_verify_login(client, capture_sent_emails, "user-two@example.com")
    await client.post("/api/v1/favorites", json={"ticker": "ZENITHBANK", "market": "NG"})

    listing = await client.get("/api/v1/favorites")
    tickers = [item["ticker"] for item in listing.json()["items"]]
    assert tickers == ["ZENITHBANK"]
