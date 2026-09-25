import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("app.email")

_SEND_URL = "https://send.api.mailtrap.io/api/send"
_FROM = {"email": "no-reply@koboandcents.com", "name": "Kobo & Cents"}


async def send_email(to: str, subject: str, html: str) -> None:
    """Every transactional email goes through here, per
    docs/backend-architecture/00.md: Mailtrap's sandbox catches
    everything in development, the same send API is used in
    production once a real domain is verified. Without a configured
    token, logs instead of calling the real API, the same
    dev-safe-by-default pattern already used for PostHog and Sentry."""
    if not settings.mailtrap_api_token:
        # Includes the body, not just the subject: without this, the
        # verification/reset link inside it is genuinely unreachable
        # in local dev, no Mailtrap sandbox and no way to click a link
        # that only exists as a database-stored hash otherwise. A real
        # gap noticed while trying to write an end-to-end test for the
        # verify flow, not obvious until actually attempting that.
        logger.info(
            "email (not sent, no MAILTRAP_API_TOKEN configured): to=%s subject=%s html=%s",
            to,
            subject,
            html,
        )
        return

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _SEND_URL,
            headers={"Authorization": f"Bearer {settings.mailtrap_api_token}"},
            json={
                "from": _FROM,
                "to": [{"email": to}],
                "subject": subject,
                "html": html,
            },
            timeout=10.0,
        )
        response.raise_for_status()


def verification_email_html(verify_url: str) -> str:
    return (
        f"<p>Confirm your email to finish creating your Kobo &amp; Cents account.</p>"
        f'<p><a href="{verify_url}">Verify your email</a></p>'
        f"<p>This link expires in 30 minutes. If you didn't request this, ignore this email.</p>"
    )


def password_reset_email_html(reset_url: str) -> str:
    return (
        f"<p>Reset your Kobo &amp; Cents password.</p>"
        f'<p><a href="{reset_url}">Choose a new password</a></p>'
        f"<p>This link expires in 30 minutes. If you didn't request this, ignore this email.</p>"
    )
