from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class FetchedFinancials:
    """The structured, schema-constrained shape every market data
    source returns, per docs/backend-architecture/00.md: whether it
    came from a provider API or the LLM research agent, the rest of
    the pipeline never has to know which. A free-text response from
    either source is a failed call, not a value to guess at parsing,
    so both integrations validate into this shape before returning."""

    ticker: str
    statement_date: datetime
    price: float | None
    current_assets: float | None
    current_liabilities: float | None
    inventory: float | None
    shareholders_equity: float | None
    shares_outstanding: float | None
    net_income: float | None
    revenue: float | None
    previous_year_revenue: float | None
    operating_profit_after_tax: float | None
    invested_capital: float | None
    cash_from_operations: float | None
    capex: float | None
    dividend_per_share: float | None
    eps: float | None
    data_source: str  # "provider" | "ng_research_agent"
    source_urls: dict[str, str] | None = None


class MarketDataProvider(Protocol):
    """Swappable behind this interface, per docs/backend-architecture/
    03-phases.md's Sub-phase 3.1, so the actual US provider (Alpha
    Vantage today) or the NG research agent can change without
    touching the refresh job that calls them. `company_name` is part
    of the shared signature even though only the research agent
    actually needs it (a provider looked up by ticker symbol alone
    has no use for it), so the refresh job can call either provider
    identically instead of branching on which one it's talking to."""

    async def fetch(self, ticker: str, company_name: str) -> FetchedFinancials: ...


class ProviderNotConfiguredError(RuntimeError):
    """Raised, not silently swallowed, when the required API key is
    missing. Unlike email or analytics, a market-data fetch failing
    silently would mean a stock's page quietly showing stale or empty
    data with no visible cause. The refresh job's own per-ticker error
    handling (Sub-phase 3.2) is what turns this into "skip this one
    ticker, keep going," not this class itself."""
