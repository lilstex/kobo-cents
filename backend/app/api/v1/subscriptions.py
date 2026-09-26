import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import READ_LIMIT, limiter
from app.core.redis import redis_client
from app.db.session import get_db
from app.integrations.payments.base import PaymentProvider, ProviderNotConfiguredError
from app.integrations.payments.flutterwave import FlutterwaveAdapter
from app.integrations.payments.paystack import PaystackAdapter
from app.schemas.subscriptions import CheckoutRequest, CheckoutResponse, EntitlementResponse
from app.services.entitlements import is_entitled

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

_PROVIDERS: dict[str, PaymentProvider] = {
    "paystack": PaystackAdapter(),
    "flutterwave": FlutterwaveAdapter(),
}

# How long a checkout reference stays mapped to the user who started
# it, in Redis, per the same "genuinely disposable, no Postgres row"
# reasoning app/api/v1/share.py already applies: a checkout either
# completes within minutes or the reference stops mattering. Generous
# enough that a slow card-issuer confirmation still resolves.
_CHECKOUT_TTL_SECONDS = 2 * 60 * 60


def _checkout_key(reference: str) -> str:
    return f"checkout:{reference}"


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
) -> CheckoutResponse:
    provider = _PROVIDERS.get(body.provider)
    if provider is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown provider: {body.provider}")

    reference = f"kc_{uuid.uuid4().hex}"
    amount = (
        settings.subscription_price_ngn
        if body.provider == "paystack"
        else settings.subscription_price_usd
    )
    currency = "NGN" if body.provider == "paystack" else "USD"

    try:
        session = await provider.create_checkout(
            email=current_user["email"],
            reference=reference,
            amount=amount,
            currency=currency,
            callback_url="https://koboandcents.com/app/settings?checkout=complete",
        )
    except ProviderNotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    await redis_client.set(
        _checkout_key(reference),
        json.dumps({"user_id": str(current_user["id"]), "provider": body.provider}),
        ex=_CHECKOUT_TTL_SECONDS,
    )
    return CheckoutResponse(redirect_url=session.redirect_url)


@router.get("/entitlement", response_model=EntitlementResponse)
@limiter.limit(READ_LIMIT)
async def get_entitlement(
    request: Request,
    feature: str = Query(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> EntitlementResponse:
    """A plain yes/no, not part of Backend Phase 6/7/8's original task
    list: Frontend Sub-phase 8.2 needs to know which empty state to
    show (free-tier Lock icon vs. the real paid-tier form) before any
    gated action is attempted, and require_feature() alone only
    answers that by way of a 402 after the fact."""
    entitled = await is_entitled(db, current_user["id"], feature)
    return EntitlementResponse(entitled=entitled)
