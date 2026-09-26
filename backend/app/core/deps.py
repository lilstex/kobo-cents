import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.session import get_session
from app.db.session import get_db
from app.models.users import users


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reads the session cookie, looks up the Redis session, per
    docs/backend-architecture/03-phases.md's Sub-phase 2.2. Used by
    every protected route from here on."""
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

    result = await db.execute(select(users).where(users.c.id == uuid.UUID(session["user_id"])))
    user = result.mappings().first()
    if user is None or user["deleted_at"] is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account no longer exists")
    return dict(user)
