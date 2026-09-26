import re

import pytest


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


async def test_login_is_rate_limited_at_the_auth_sensitive_tier(
    client, db_session, capture_sent_emails
):
    """Sub-phase 10.1 of docs/backend-architecture/03-phases.md: login
    had no rate limit at all before this, a real gap, credential
    stuffing is exactly the risk a per-IP limit on this endpoint
    defends against."""
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "rl-login@example.com",
            "password": "a-real-password",
            "terms_version": "v1",
        },
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})

    for _ in range(10):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "rl-login@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": "rl-login@example.com", "password": "wrong-password"},
    )
    assert blocked.status_code == 429


async def test_market_overview_is_rate_limited_at_the_read_tier(
    client, db_session, capture_sent_emails
):
    """The general rate limiting Sub-phase 10.1 asks for, not just
    signup and share-link creation: a scripted, authenticated account
    hammering a read endpoint should hit a real ceiling too, per
    docs/01_product.md's abuse mitigation section.

    Authenticated, deliberately: SlowAPI's limit decorator wraps the
    route function's body, which FastAPI never calls at all when a
    Depends() (get_current_user, here) raises first, so an
    unauthenticated request never reaches the counter in the first
    place, real behavior confirmed by first writing this test against
    an unauthenticated client and watching it never hit 429."""
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "rl-overview@example.com",
            "password": "a-real-password",
            "terms_version": "v1",
        },
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rl-overview@example.com", "password": "a-real-password"},
    )

    for _ in range(120):
        response = await client.get("/api/v1/markets/NG/overview")
        assert response.status_code == 200

    blocked = await client.get("/api/v1/markets/NG/overview")
    assert blocked.status_code == 429
