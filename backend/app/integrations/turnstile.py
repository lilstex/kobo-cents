import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("app.turnstile")

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str) -> bool:
    """Called on signup, per docs/backend-architecture/00.md's abuse
    mitigation section. Without a configured secret, passes
    everything through, the same dev-safe-by-default pattern used
    elsewhere; there is no Turnstile site configured yet to actually
    check against."""
    if not settings.turnstile_secret_key:
        logger.info("turnstile check skipped, no TURNSTILE_SECRET_KEY configured")
        return True

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _VERIFY_URL,
            data={"secret": settings.turnstile_secret_key, "response": token},
            timeout=10.0,
        )
        response.raise_for_status()
        return bool(response.json().get("success"))
