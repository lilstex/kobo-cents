import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import AUTH_SENSITIVE_LIMIT, limiter
from app.core.security import hash_password, verify_password
from app.core.session import delete_all_sessions_for_user
from app.db.session import get_db
from app.models.users import users
from app.schemas.account import DeleteAccountRequest
from app.schemas.auth import MessageResponse

router = APIRouter(tags=["account"])


@router.delete("/account", response_model=MessageResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def delete_account(
    request: Request,
    response: Response,
    body: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Sub-phase 10.4: a soft delete, not a hard DELETE, per docs/
    backend-architecture/02.md, sets deleted_at and anonymizes the
    users row's personal fields, leaves subscriptions and
    payment_events untouched (likely needed for accounting purposes
    regardless of what a user asked deleted about their own profile).
    The exact retention period before an anonymized row is ever purged
    for good is a real, still-open NDPR question, per 02.md's explicit
    instruction not to guess at it here; this endpoint is the request
    mechanism, correct regardless of what that period turns out to be.

    A hijacked session cookie alone can't trigger this: the current
    password is required too, the same extra confirmation change-
    password already asks for, since this action can't be undone by
    logging back in the way a password change can."""
    if not verify_password(body.password, current_user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")

    now = datetime.now(UTC)
    anonymized_email = f"deleted-{current_user['id']}@koboandcents.invalid"
    await db.execute(
        update(users)
        .where(users.c.id == current_user["id"])
        .values(
            deleted_at=now,
            email=anonymized_email,
            # A random value, never stored anywhere as plaintext, not
            # even in this request: whatever password existed before
            # is now permanently unusable, matching deleted_at's intent
            # that this account can never log in again.
            password_hash=hash_password(secrets.token_urlsafe(32)),
        )
    )
    await db.commit()

    # Covers the current session too, per delete_all_sessions_for_user's
    # own scan, the same single call reset_password already relies on
    # rather than also separately deleting "this" session.
    await delete_all_sessions_for_user(str(current_user["id"]))
    response.delete_cookie(settings.session_cookie_name)
    response.delete_cookie("has_session")

    return MessageResponse(message="Account deleted")
