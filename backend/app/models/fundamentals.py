import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Numeric, String, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import metadata

# A real gap caught while actually building Phase 3, not part of the
# original Phase 1 pass: stock_scores_current/history hold *derived*
# numbers, and stock_prices_current/history hold price, but nowhere
# stored the raw figures (net income, shareholders' equity, and so on)
# that app/services/scoring.py actually turns into those percentiles.
# Same _current/_history split as everything else, per 02.md, plus the
# provenance fields the LLM research agent mechanism from 00.md needs:
# which source produced this row, whether it needs a human look before
# being trusted, and the URL behind every figure it drew.


def _fundamental_columns() -> list[Column]:
    """A fresh list of Column objects per call: SQLAlchemy binds a
    Column instance to its parent Table the moment it's assigned, so
    the same instances can't be reused across the two tables below,
    a real error caught by actually running the migration, not
    something obvious from reading the code alone."""
    return [
        Column("statement_date", DateTime(timezone=True), nullable=False),
        Column("current_assets", Numeric, nullable=True),
        Column("current_liabilities", Numeric, nullable=True),
        Column("inventory", Numeric, nullable=True),
        Column("shareholders_equity", Numeric, nullable=True),
        Column("shares_outstanding", Numeric, nullable=True),
        Column("net_income", Numeric, nullable=True),
        Column("revenue", Numeric, nullable=True),
        Column("previous_year_revenue", Numeric, nullable=True),
        Column("operating_profit_after_tax", Numeric, nullable=True),
        Column("invested_capital", Numeric, nullable=True),
        Column("cash_from_operations", Numeric, nullable=True),
        Column("capex", Numeric, nullable=True),
        Column("dividend_per_share", Numeric, nullable=True),
        Column("eps", Numeric, nullable=True),
        # "provider" (Alpha Vantage/FMP/Polygon) or "ng_research_agent"
        # (the LLM web-search mechanism, per 00.md), per figure set,
        # not per individual field, since one research-agent call
        # returns the whole set together.
        Column("data_source", String, nullable=False),
        # The sanity-check gate from 01.md's alert-matching logic,
        # reused here per 00.md: a figure that moved past a meaningful
        # delta since the last cycle gets flagged instead of silently
        # trusted.
        Column("needs_review", Boolean, nullable=False, default=False),
        # Every figure's source URL, only meaningful for
        # data_source="ng_research_agent", per 00.md's citation
        # requirement.
        Column("source_urls", JSONB, nullable=True),
    ]


stock_fundamentals_current = Table(
    "stock_fundamentals_current",
    metadata,
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), primary_key=True),
    *_fundamental_columns(),
    Column("last_successful_refresh_at", DateTime(timezone=True), nullable=False),
)

stock_fundamentals_history = Table(
    "stock_fundamentals_history",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("stock_id", UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False),
    *_fundamental_columns(),
    Column("recorded_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("ix_stock_fundamentals_history_stock_id_recorded_at", "stock_id", "recorded_at"),
)
