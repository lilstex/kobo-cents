import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import metadata

# Sub-phase 1.2: market data tables, per docs/backend-architecture/02.md.
# stocks is the stable master-data table everything else foreign-keys
# against; scores and prices each split into a _current table (upserted
# every refresh cycle, what the app actually reads) and a history table
# (append-only, what trend language and charts read from), resolving
# the ambiguity 01.md originally left open.

stocks = Table(
    "stocks",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("ticker", String, nullable=False),
    Column("company_name", String, nullable=False),
    Column("market", String, nullable=False),  # "NG" or "US"
    Column("sector", String, nullable=False),
    Column("listing_status", String, nullable=False, default="active"),
    UniqueConstraint("ticker", "market", name="uq_stocks_ticker_market"),
    # Trigram indexes for Sub-phase 4.3's fuzzy search, per 01.md: a
    # typo-tolerant "zenit" still finds Zenith Bank. Requires the
    # pg_trgm extension, enabled in the migration that creates these.
    Index(
        "ix_stocks_ticker_trgm",
        "ticker",
        postgresql_using="gin",
        postgresql_ops={"ticker": "gin_trgm_ops"},
    ),
    Index(
        "ix_stocks_company_name_trgm",
        "company_name",
        postgresql_using="gin",
        postgresql_ops={"company_name": "gin_trgm_ops"},
    ),
)

stock_scores_current = Table(
    "stock_scores_current",
    metadata,
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), primary_key=True),
    Column("composite_score", Numeric, nullable=False),
    Column("bucket", String, nullable=False),  # "well" | "potential" | "under"
    # Per-metric percentile and weighted contribution, per 01.md, read
    # as one unit by the explainability panel, never queried
    # metric-by-metric in SQL.
    Column("metric_detail", JSONB, nullable=False),
    Column("weights_version", String, ForeignKey("scoring_weights.version"), nullable=False),
    Column("computed_at", DateTime(timezone=True), nullable=False),
    # Per-stock staleness, per 02.md: distinct from a global refresh
    # timestamp, so one failed ticker doesn't make every other stock's
    # page lie about how current its data is.
    Column("last_successful_refresh_at", DateTime(timezone=True), nullable=False),
)

stock_scores_history = Table(
    "stock_scores_history",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False),
    Column("composite_score", Numeric, nullable=False),
    Column("bucket", String, nullable=False),
    Column("metric_detail", JSONB, nullable=False),
    Column("weights_version", String, ForeignKey("scoring_weights.version"), nullable=False),
    Column("computed_at", DateTime(timezone=True), nullable=False),
    Index("ix_stock_scores_history_stock_id_computed_at", "stock_id", "computed_at"),
)

stock_prices_current = Table(
    "stock_prices_current",
    metadata,
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), primary_key=True),
    Column("price", Numeric, nullable=False),
    Column("change_percent", Numeric, nullable=False),
    # Same provenance fields as stock_fundamentals_current, per 00.md:
    # for an NG stock, price comes from the same research-agent call
    # as the fundamentals, not a separately-trusted source.
    Column("data_source", String, nullable=False),
    Column("needs_review", Boolean, nullable=False, default=False),
    Column("last_successful_refresh_at", DateTime(timezone=True), nullable=False),
)

price_history = Table(
    "price_history",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False),
    # OHLC, per 01.md: what the price chart actually renders from, not
    # just a single point per cycle.
    Column("open", Numeric, nullable=False),
    Column("high", Numeric, nullable=False),
    Column("low", Numeric, nullable=False),
    Column("close", Numeric, nullable=False),
    Column("volume", Numeric, nullable=True),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Index("ix_price_history_stock_id_recorded_at", "stock_id", "recorded_at"),
)

scoring_weights = Table(
    "scoring_weights",
    metadata,
    Column("version", String, primary_key=True),
    # Metric-within-category and category-within-composite weights,
    # per 01.md: config-driven, never hardcoded in the scoring function.
    Column("metric_weights", JSONB, nullable=False),
    Column("category_weights", JSONB, nullable=False),
    Column("is_active", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
