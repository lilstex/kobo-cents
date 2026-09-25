import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import metadata

# Sub-phase 1.4: payments and subscriptions, per
# docs/backend-architecture/02.md. Real tables, not a boolean on the
# user row and not just signature verification: subscription state
# needs "since when, through when, which provider" to answer a refund
# or support question, and payment_events is the webhook idempotency
# mechanism, distinct from trusting a webhook's signature.

subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("provider", String, nullable=False),  # "paystack" | "flutterwave"
    Column("provider_subscription_id", String, nullable=False),
    Column("status", String, nullable=False),  # "active" | "canceled" | "expired"
    Column("current_period_end", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

payment_events = Table(
    "payment_events",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("provider", String, nullable=False),
    Column("provider_event_id", String, nullable=False),
    Column("event_type", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("processed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    # The idempotency mechanism itself: insert the event id first, and
    # a unique-violation means it was already processed, skip it
    # rather than double-crediting a subscription.
    UniqueConstraint("provider", "provider_event_id", name="uq_payment_events_provider_event"),
)
