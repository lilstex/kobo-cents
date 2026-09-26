import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.subscriptions import _checkout_key
from app.core.redis import redis_client
from app.db.session import get_db
from app.integrations.payments.base import PaymentProvider
from app.integrations.payments.flutterwave import FlutterwaveAdapter
from app.integrations.payments.paystack import PaystackAdapter
from app.models.payments import payment_events
from app.workers.tasks.subscription_tasks import activate_subscription_task

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _handle_webhook(
    db: AsyncSession, provider_name: str, provider: PaymentProvider, raw_body: bytes, headers: dict
) -> None:
    """Only the fast, synchronous part happens here: signature
    verification and the payment_events idempotency insert, per
    docs/backend-architecture/00.md's own framing ("processing payment
    webhooks... with retries if a failed webhook, no separate worker
    process so a slow job can't" block the response the provider is
    waiting on). The actual subscription update is dispatched to
    activate_subscription_task (Sub-phase 10.2's retry-with-backoff),
    not run inline, so a slow or transiently-failing DB write never
    delays the 200 the provider needs back quickly."""
    if not provider.verify_webhook_signature(raw_body, headers):
        # Per docs/backend-architecture/00.md: skipping this check
        # would let anyone who finds the webhook URL POST a fake
        # "payment successful" event and get a free subscription.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")

    payload = json.loads(raw_body)
    event = provider.parse_webhook_event(payload)

    # Idempotency, distinct from signature verification, per 02.md:
    # insert the event id first, relying on the unique constraint. A
    # conflict means this exact event was already processed, a
    # provider redelivery, not a new payment, acknowledge and stop.
    inserted = await db.execute(
        pg_insert(payment_events)
        .values(
            id=uuid.uuid4(),
            provider=provider_name,
            provider_event_id=event.event_id,
            event_type=event.event_type,
            payload=payload,
        )
        .on_conflict_do_nothing(index_elements=["provider", "provider_event_id"])
        .returning(payment_events.c.id)
    )
    if inserted.first() is None:
        await db.commit()
        return
    await db.commit()

    if event.status != "successful":
        return

    checkout_raw = await redis_client.get(_checkout_key(event.reference))
    if checkout_raw is None:
        # The reference doesn't map to a checkout this backend
        # started (expired, or a provider retry long after the TTL
        # window), nothing to credit, and nothing to retry either.
        return
    checkout = json.loads(checkout_raw)
    activate_subscription_task.delay(checkout["user_id"], provider_name, event.reference)


@router.post("/paystack", status_code=status.HTTP_200_OK)
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    raw_body = await request.body()
    await _handle_webhook(db, "paystack", PaystackAdapter(), raw_body, dict(request.headers))
    return {"status": "ok"}


@router.post("/flutterwave", status_code=status.HTTP_200_OK)
async def flutterwave_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    raw_body = await request.body()
    await _handle_webhook(db, "flutterwave", FlutterwaveAdapter(), raw_body, dict(request.headers))
    return {"status": "ok"}
