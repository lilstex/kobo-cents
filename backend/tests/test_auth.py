import re

import pytest

from app.core.session import get_session


@pytest.fixture(autouse=True)
def capture_sent_emails(monkeypatch):
    """Never actually sends anything (no MAILTRAP_API_TOKEN in test
    config anyway), and captures every call so a test can pull the
    real token out of the URL that would have been emailed, the only
    place the raw (unhashed) token exists outside the request/response
    cycle itself."""
    sent = []

    def fake_delay(to, subject, html):
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.api.v1.auth.send_email_task.delay", fake_delay)
    return sent


def _extract_token(html: str) -> str:
    match = re.search(r"token=([^\"&]+)", html)
    assert match, f"no token found in: {html}"
    return match.group(1)


async def _signup(client, email="new-user@example.com", password="a-real-password"):
    return await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "terms_version": "v1"},
    )


async def test_signup_creates_an_unverified_account(client, capture_sent_emails):
    response = await _signup(client)
    assert response.status_code == 201
    assert response.json() == {"email": "new-user@example.com", "verified": False}
    assert len(capture_sent_emails) == 1
    assert capture_sent_emails[0]["to"] == "new-user@example.com"


async def test_signup_rejects_a_duplicate_email(client):
    await _signup(client, email="dup@example.com")
    response = await _signup(client, email="dup@example.com")
    assert response.status_code == 409


async def test_signup_rejects_a_short_password(client):
    response = await _signup(client, password="short")
    assert response.status_code == 422


async def test_verify_activates_the_account_and_the_token_is_single_use(
    client, capture_sent_emails
):
    await _signup(client, email="verify-me@example.com")
    token = _extract_token(capture_sent_emails[0]["html"])

    first = await client.post("/api/v1/auth/verify", json={"token": token})
    assert first.status_code == 200

    second = await client.post("/api/v1/auth/verify", json={"token": token})
    assert second.status_code == 400


async def test_verify_rejects_a_garbage_token(client):
    response = await client.post("/api/v1/auth/verify", json={"token": "not-a-real-token"})
    assert response.status_code == 400


async def test_login_before_verification_returns_unverified_not_a_generic_failure(client):
    await _signup(client, email="unverified@example.com", password="a-real-password")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "a-real-password"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "unverified"}
    assert "kc_session" not in response.cookies


async def test_login_with_wrong_password_is_rejected(client):
    await _signup(client, email="someone@example.com", password="a-real-password")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "someone@example.com", "password": "the-wrong-password"},
    )
    assert response.status_code == 401


async def test_login_after_verification_sets_a_session_cookie(client, capture_sent_emails):
    await _signup(client, email="verified-login@example.com", password="a-real-password")
    token = _extract_token(capture_sent_emails[0]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "verified-login@example.com", "password": "a-real-password"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    session_id = response.cookies.get("kc_session")
    assert session_id
    assert await get_session(session_id) is not None
    # The frontend's route-protection middleware and header swap read
    # this plain, non-httpOnly cookie, per docs/frontend-architecture/
    # 04-landing-page-indepth.md: a UX hint only, never trusted for
    # the real access check, which is the httpOnly session above.
    assert response.cookies.get("has_session") == "1"


async def test_logout_deletes_the_session(client, capture_sent_emails):
    await _signup(client, email="logout-me@example.com", password="a-real-password")
    token = _extract_token(capture_sent_emails[0]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout-me@example.com", "password": "a-real-password"},
    )
    session_id = login_response.cookies.get("kc_session")

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    assert await get_session(session_id) is None
    assert "has_session" not in logout_response.cookies


async def test_change_password_requires_the_correct_current_password(client, capture_sent_emails):
    await _signup(client, email="change-pw@example.com", password="the-original-password")
    token = _extract_token(capture_sent_emails[0]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    await client.post(
        "/api/v1/auth/login",
        json={"email": "change-pw@example.com", "password": "the-original-password"},
    )

    wrong = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "not-the-real-one", "new_password": "a-new-password"},
    )
    assert wrong.status_code == 401

    right = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "the-original-password", "new_password": "a-new-password"},
    )
    assert right.status_code == 200


async def test_forgot_password_gives_the_same_response_whether_or_not_the_account_exists(client):
    real_user_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "someone@example.com"}
    )
    nobody_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody-at-all@example.com"}
    )
    assert real_user_response.status_code == nobody_response.status_code == 200
    assert real_user_response.json() == nobody_response.json()


async def test_reset_password_invalidates_existing_sessions(client, capture_sent_emails):
    await _signup(client, email="reset-me@example.com", password="the-old-password")
    verify_token = _extract_token(capture_sent_emails[0]["html"])
    await client.post("/api/v1/auth/verify", json={"token": verify_token})
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-me@example.com", "password": "the-old-password"},
    )
    session_id = login_response.cookies.get("kc_session")

    await client.post("/api/v1/auth/forgot-password", json={"email": "reset-me@example.com"})
    reset_token = _extract_token(capture_sent_emails[-1]["html"])
    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "a-brand-new-password"},
    )
    assert reset_response.status_code == 200
    assert await get_session(session_id) is None

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-me@example.com", "password": "the-old-password"},
    )
    assert old_login.status_code == 401


async def test_signup_is_rate_limited_per_ip(client):
    for _ in range(5):
        response = await _signup(client, email=f"limit-{_}@example.com")
        assert response.status_code == 201

    blocked = await _signup(client, email="limit-6@example.com")
    assert blocked.status_code == 429
