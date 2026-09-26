import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import AUTH_SENSITIVE_LIMIT, WRITE_LIMIT, limiter
from app.core.security import hash_password, verify_password
from app.core.session import create_session, delete_all_sessions_for_user, delete_session
from app.core.tokens import generate_token, hash_token
from app.db.session import get_db
from app.integrations.email.mailtrap import (
    password_reset_email_html,
    verification_email_html,
)
from app.integrations.turnstile import verify_turnstile
from app.models.users import password_reset_tokens, users, verification_tokens
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    VerifyRequest,
)
from app.workers.tasks.email_tasks import send_email_task

router = APIRouter(prefix="/auth", tags=["auth"])

_TOKEN_TTL = timedelta(minutes=30)
_MIN_PASSWORD_LENGTH = 8


def _now() -> datetime:
    return datetime.now(UTC)


async def _issue_token(db: AsyncSession, table, user_id: uuid.UUID) -> str:
    token = generate_token()
    await db.execute(
        table.insert().values(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=hash_token(token),
            expires_at=_now() + _TOKEN_TTL,
        )
    )
    return token


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def signup(request: Request, body: SignupRequest, db: AsyncSession = Depends(get_db)):
    if len(body.password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters",
        )
    if not await verify_turnstile(body.turnstile_token):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Verification challenge failed")

    existing = await db.execute(select(users.c.id).where(users.c.email == body.email))
    if existing.first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user_id = uuid.uuid4()
    await db.execute(
        users.insert().values(
            id=user_id,
            email=body.email,
            password_hash=hash_password(body.password),
            email_verified=False,
            terms_accepted_version=body.terms_version,
            terms_accepted_at=_now(),
        )
    )
    token = await _issue_token(db, verification_tokens, user_id)
    await db.commit()

    send_email_task.delay(
        body.email,
        "Verify your Kobo & Cents account",
        verification_email_html(f"https://koboandcents.com/verify?token={token}"),
    )
    return SignupResponse(email=body.email, verified=False)


@router.post("/verify", response_model=MessageResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def verify(request: Request, body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(body.token)
    result = await db.execute(
        select(verification_tokens).where(verification_tokens.c.token_hash == token_hash)
    )
    record = result.mappings().first()
    if record is None or record["used_at"] is not None or record["expires_at"] < _now():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This verification link is invalid or has expired"
        )

    await db.execute(
        update(verification_tokens)
        .where(verification_tokens.c.id == record["id"])
        .values(used_at=_now())
    )
    await db.execute(
        update(users).where(users.c.id == record["user_id"]).values(email_verified=True)
    )
    await db.commit()
    return MessageResponse(message="Email verified")


@router.post("/login", response_model=LoginResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def login(
    request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(users).where(users.c.email == body.email))
    user = result.mappings().first()
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not user["email_verified"]:
        # Not a generic auth failure, per docs/backend-architecture/
        # 03-phases.md: the frontend uses this specific status to
        # redirect to the verification screen instead.
        return LoginResponse(status="unverified")

    session_id = await create_session(str(user["id"]))
    response.set_cookie(
        settings.session_cookie_name,
        session_id,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        # Secure means "never sent over plain HTTP," which is exactly
        # right for production but breaks local dev, which runs over
        # http://localhost, not https. A browser (and httpx's cookie
        # jar, correctly, which is how this got caught) drops a Secure
        # cookie silently on an insecure connection rather than erroring.
        secure=settings.app_env != "development",
        samesite="lax",
    )
    # A second, non-sensitive, readable cookie, per
    # docs/frontend-architecture/04-landing-page-indepth.md: the
    # frontend's own middleware and header swap read this to decide
    # what to render, without needing a server round trip against the
    # real session. It's a UX hint only, never a security boundary,
    # every actual protected read still checks the real session above.
    response.set_cookie(
        "has_session",
        "1",
        max_age=settings.session_ttl_seconds,
        httponly=False,
        secure=settings.app_env != "development",
        samesite="lax",
    )
    return LoginResponse(status="ok")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def resend_verification(
    request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(users).where(users.c.email == body.email, users.c.email_verified.is_(False))
    )
    user = result.mappings().first()
    if user is not None:
        token = await _issue_token(db, verification_tokens, user["id"])
        await db.commit()
        send_email_task.delay(
            user["email"],
            "Verify your Kobo & Cents account",
            verification_email_html(f"https://koboandcents.com/verify?token={token}"),
        )
    # Same response either way, same anti-enumeration reasoning as
    # forgot-password below.
    return MessageResponse(message="If that account needs verifying, a new email is on its way")


@router.post("/logout", response_model=MessageResponse)
@limiter.limit(WRITE_LIMIT)
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        await delete_session(session_id)
    response.delete_cookie(settings.session_cookie_name)
    response.delete_cookie("has_session")
    return MessageResponse(message="Logged out")


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")
    if len(body.new_password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters",
        )
    await db.execute(
        update(users)
        .where(users.c.id == current_user["id"])
        .values(password_hash=hash_password(body.new_password))
    )
    await db.commit()
    return MessageResponse(message="Password changed")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/hour")
async def forgot_password(
    request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(users).where(users.c.email == body.email))
    user = result.mappings().first()
    if user is not None:
        token = await _issue_token(db, password_reset_tokens, user["id"])
        await db.commit()
        send_email_task.delay(
            user["email"],
            "Reset your Kobo & Cents password",
            password_reset_email_html(f"https://koboandcents.com/reset-password?token={token}"),
        )
    # Always the same response, per docs/backend-architecture/00.md:
    # whether or not the email exists never leaks through a response
    # difference.
    return MessageResponse(message="If that account exists, a reset email is on its way")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(AUTH_SENSITIVE_LIMIT)
async def reset_password(
    request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    if len(body.new_password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters",
        )
    token_hash = hash_token(body.token)
    result = await db.execute(
        select(password_reset_tokens).where(password_reset_tokens.c.token_hash == token_hash)
    )
    record = result.mappings().first()
    if record is None or record["used_at"] is not None or record["expires_at"] < _now():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This reset link is invalid or has expired"
        )

    await db.execute(
        update(password_reset_tokens)
        .where(password_reset_tokens.c.id == record["id"])
        .values(used_at=_now())
    )
    await db.execute(
        update(users)
        .where(users.c.id == record["user_id"])
        .values(password_hash=hash_password(body.new_password))
    )
    await db.commit()
    # Every existing session for this user dies here too, per
    # docs/backend-architecture/00.md, not just the reset token.
    await delete_all_sessions_for_user(str(record["user_id"]))
    return MessageResponse(message="Password reset")
