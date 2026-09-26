import re

import pytest
from sqlalchemy import select

from app.core.session import get_session
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


async def _signup_verify_login(client, capture_sent_emails, email: str, password: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "terms_version": "v1"},
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.cookies.get("kc_session")


async def test_delete_account_requires_authentication(client, db_session):
    response = await client.request("DELETE", "/api/v1/account", json={"password": "whatever"})
    assert response.status_code == 401


async def test_delete_account_requires_the_correct_password(
    client, db_session, capture_sent_emails
):
    await _signup_verify_login(
        client, capture_sent_emails, "delete-wrong-pw@example.com", "the-real-password"
    )
    response = await client.request(
        "DELETE", "/api/v1/account", json={"password": "not-the-real-password"}
    )
    assert response.status_code == 401

    # The account is still very much alive.
    row = (
        await db_session.execute(
            select(users.c.deleted_at).where(users.c.email == "delete-wrong-pw@example.com")
        )
    ).scalar_one()
    assert row is None


async def test_delete_account_anonymizes_the_row_and_kills_the_session(
    client, db_session, capture_sent_emails
):
    session_id = await _signup_verify_login(
        client, capture_sent_emails, "delete-me@example.com", "the-real-password"
    )
    user_id = (
        await db_session.execute(select(users.c.id).where(users.c.email == "delete-me@example.com"))
    ).scalar_one()

    response = await client.request(
        "DELETE", "/api/v1/account", json={"password": "the-real-password"}
    )
    assert response.status_code == 200

    row = (
        (
            await db_session.execute(
                select(users.c.deleted_at, users.c.email).where(users.c.id == user_id)
            )
        )
        .mappings()
        .first()
    )
    assert row["deleted_at"] is not None
    assert row["email"].endswith("@koboandcents.invalid")

    # The real Redis session this request's cookie referenced is gone.
    assert await get_session(session_id) is None


async def test_deleted_account_can_no_longer_log_in(client, db_session, capture_sent_emails):
    await _signup_verify_login(
        client, capture_sent_emails, "delete-then-login@example.com", "the-real-password"
    )
    await client.request("DELETE", "/api/v1/account", json={"password": "the-real-password"})

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete-then-login@example.com", "password": "the-real-password"},
    )
    # The email itself was anonymized, so this now reads as "no such
    # account," the same response shape as any other unknown email,
    # never a distinct "this account was deleted" signal.
    assert response.status_code == 401
