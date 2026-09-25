import json
import secrets

from app.core.config import settings
from app.core.redis import redis_client

# Server-side sessions in Redis, not JWT, per docs/backend-architecture/
# 00.md: instant revocation (log out everywhere, kill a compromised
# account's sessions) without needing a token blocklist.


def _key(session_id: str) -> str:
    return f"session:{session_id}"


async def create_session(user_id: str) -> str:
    session_id = secrets.token_urlsafe(32)
    await redis_client.set(
        _key(session_id),
        json.dumps({"user_id": user_id}),
        ex=settings.session_ttl_seconds,
    )
    return session_id


async def get_session(session_id: str) -> dict | None:
    raw = await redis_client.get(_key(session_id))
    if raw is None:
        return None
    return json.loads(raw)


async def delete_session(session_id: str) -> None:
    await redis_client.delete(_key(session_id))


async def delete_all_sessions_for_user(user_id: str) -> None:
    """Used on password reset, per docs/backend-architecture/03-phases.md:
    a reset invalidates every existing session for that user, not just
    the token. Scans rather than maintaining a secondary index, an
    acceptable tradeoff at this scale; revisit if the session count
    ever makes a SCAN pass itself the bottleneck."""
    async for key in redis_client.scan_iter(match="session:*"):
        raw = await redis_client.get(key)
        if raw and json.loads(raw).get("user_id") == user_id:
            await redis_client.delete(key)
