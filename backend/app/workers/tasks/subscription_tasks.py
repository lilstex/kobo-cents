import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.payments import subscriptions
from app.workers.celery import celery_app

# A one-time, 30-day charge, not a recurring-billing API integration,
# per app/api/v1/webhooks.py's own reasoning: simpler, and enough for
# what docs/backend-architecture/00.md actually asks for at this
# stage. A real renewal/dunning flow is a separate, later task, see
# docs/open-items.md.
_SUBSCRIPTION_PERIOD_DAYS = 30


async def activate_subscription(
    db: AsyncSession, user_id: uuid.UUID, provider_name: str, reference: str
) -> None:
    """Takes an injected session rather than creating one, per the
    same pattern app/workers/tasks/refresh_market_data.py's
    refresh_market() already established: a test can hand this the
    same rolled-back-transaction session tests/conftest.py uses
    everywhere else, real database round trips, nothing left over
    once the test ends. Committing is the caller's job."""
    now = datetime.now(UTC)
    new_period_end = now + timedelta(days=_SUBSCRIPTION_PERIOD_DAYS)

    existing = await db.execute(
        select(subscriptions).where(
            subscriptions.c.user_id == user_id, subscriptions.c.provider == provider_name
        )
    )
    row = existing.mappings().first()
    if row:
        # Extend from whichever is later: the new period, or an
        # existing subscription that hasn't actually lapsed yet.
        period_end = max(new_period_end, row["current_period_end"])
        await db.execute(
            subscriptions.update()
            .where(subscriptions.c.id == row["id"])
            .values(status="active", current_period_end=period_end)
        )
    else:
        await db.execute(
            subscriptions.insert().values(
                id=uuid.uuid4(),
                user_id=user_id,
                provider=provider_name,
                provider_subscription_id=reference,
                status="active",
                current_period_end=new_period_end,
            )
        )


async def _run_activate_subscription(
    user_id: uuid.UUID, provider_name: str, reference: str
) -> None:
    async with async_session_factory() as db:
        await activate_subscription(db, user_id, provider_name, reference)
        await db.commit()


@celery_app.task(
    name="activate_subscription",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def activate_subscription_task(user_id: str, provider_name: str, reference: str) -> None:
    """Dispatched from app/api/v1/webhooks.py after the fast,
    synchronous part (signature verification, the payment_events
    idempotency insert) already succeeded, per docs/backend-
    architecture/00.md's own framing ("processing payment webhooks...
    with retries if a failed webhook, no separate worker process so a
    slow job can't" block the webhook response the provider is
    waiting on). Retried with backoff on a genuine transient failure
    (a DB blip), per Sub-phase 10.2 of docs/backend-architecture/
    03-phases.md."""
    asyncio.run(_run_activate_subscription(uuid.UUID(user_id), provider_name, reference))
