import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.favorites import _favorites_select
from app.core.numeric import floatify
from app.core.rate_limit import WRITE_LIMIT, limiter
from app.core.redis import redis_client
from app.db.session import get_db
from app.schemas.share import CreateShareResponse, ShareSnapshotItem, ShareView
from app.services.entitlements import require_feature

router = APIRouter(prefix="/share", tags=["share"])

# 24 hours, per docs/backend-architecture/02.md: enforced by Redis's
# own TTL, not a stored expires_at column checked on every read, so
# expiry needs no separate cleanup job, the key is just gone.
_SHARE_TTL_SECONDS = 24 * 60 * 60


def _share_key(token: str) -> str:
    return f"share:{token}"


@router.post("", response_model=CreateShareResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(WRITE_LIMIT)
async def create_share(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_feature("sharing")),
) -> CreateShareResponse:
    """Snapshots the caller's favorites list as it exists right now,
    per 01_product.md: "here's what I'm watching right now," not a
    live view that would keep drifting for the 24 hours the link
    stays valid. No Postgres row, per 02.md, this data is inherently
    disposable and doesn't need to survive a service restart the way
    a user's actual account data does."""
    result = await db.execute(_favorites_select(current_user["id"]))
    items = [
        ShareSnapshotItem(**{k: v for k, v in floatify(dict(row)).items() if k != "stock_id"})
        for row in result.mappings().all()
    ]

    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    snapshot = ShareView(items=items, created_at=now)
    await redis_client.set(_share_key(token), snapshot.model_dump_json(), ex=_SHARE_TTL_SECONDS)

    return CreateShareResponse(
        token=token,
        share_url=f"https://koboandcents.com/share/{token}",
        expires_at=now + timedelta(seconds=_SHARE_TTL_SECONDS),
    )


@router.get("/{token}", response_model=ShareView)
@limiter.limit("30/hour")
async def get_share(request: Request, token: str) -> ShareView:
    """Unauthenticated on purpose, per 01_product.md: anyone with the
    link can view it, no login needed on their end. Rate-limited per
    IP against enumeration, per Sub-phase 7.2, since a token is the
    only thing standing between a guess and someone else's favorites
    list. A missing key reads as 404 whether it never existed or
    already expired, Redis has already deleted it either way, no
    separate expiry check needed."""
    raw = await redis_client.get(_share_key(token))
    if raw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This share link is invalid or has expired")
    return ShareView(**json.loads(raw))
