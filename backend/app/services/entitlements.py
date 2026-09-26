from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics import feature_flag_enabled
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.payments import subscriptions

# One reusable check, not reimplemented per gated endpoint, per
# docs/backend-architecture/02.md: every route in Phase 6 (Alerts) and
# Phase 7 (Sharing) depends on the same require_feature() rather than
# each growing its own `if user.is_paid` copy that could drift out of
# sync with the others over time.


async def _has_active_subscription(db: AsyncSession, user_id) -> bool:
    result = await db.execute(
        select(subscriptions.c.id)
        .where(
            subscriptions.c.user_id == user_id,
            subscriptions.c.status == "active",
            subscriptions.c.current_period_end > datetime.now(UTC),
        )
        .limit(1)
    )
    return result.first() is not None


async def is_entitled(db: AsyncSession, user_id, feature: str) -> bool:
    """The same check require_feature() enforces, exposed as a plain
    yes/no so a UI can ask "is this user entitled" before attempting a
    gated action, per Frontend Sub-phase 8.2's free-tier-vs-paid-tier
    states: knowing which empty state to show can't wait for a failed
    POST's 402 to find out."""
    if feature_flag_enabled(f"feature-{feature}", str(user_id)):
        return True
    return await _has_active_subscription(db, user_id)


def require_feature(feature: str):
    """Returns a FastAPI dependency gating one named feature, used as
    Depends(require_feature("alerts")). A PostHog feature flag
    (feature-{feature}) can override the subscription check for
    staged rollout, per 02.md; the flag is checked first so a granted
    override never needs a real subscription row to also exist."""

    async def _check(
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if await is_entitled(db, current_user["id"], feature):
            return current_user
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"This feature requires a paid subscription: {feature}",
        )

    return _check
