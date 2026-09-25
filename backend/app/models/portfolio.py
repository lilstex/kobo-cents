import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import metadata

# Sub-phase 1.3: user-generated data, per docs/backend-architecture/01.md
# and docs/01_product.md. Share links get no table here on purpose,
# per 02.md, they live entirely in Redis with a native TTL.

favorites = Table(
    "favorites",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False),
    # A tag, not an event history: one row per user-stock pair, not
    # one row per action, per 01.md, matching the explicit non-goal
    # against trade-lot accounting.
    Column("status", String, nullable=False),  # "watching" | "owned"
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("user_id", "stock_id", name="uq_favorites_user_stock"),
    # user_id alone is already served by the unique constraint's
    # leftmost column; stock_id needs its own index, it isn't the
    # leftmost column of that composite and this is exactly the lookup
    # the alert-matching design in 01.md depends on.
    Index("ix_favorites_stock_id", "stock_id"),
)

alerts = Table(
    "alerts",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False),
    Column("rule_type", String, nullable=False),  # "score_change" | "price_threshold"
    # The specific threshold/params for this rule, shaped differently
    # per rule_type, per 01_product.md.
    Column("rule_config", JSONB, nullable=False),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    # The exact lookup path from 01.md's alert-matching design: after
    # a refresh flags which stocks changed, find every alert on that
    # stock without scanning every user.
    Index("ix_alerts_stock_id", "stock_id"),
)
