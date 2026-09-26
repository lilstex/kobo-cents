from datetime import UTC, datetime

from app.integrations.market_data.base import FetchedFinancials
from app.integrations.market_data.cache import cache_fetch, get_cached_fetch


async def test_cache_round_trips_a_real_fetched_result():
    result = FetchedFinancials(
        ticker="GTCO",
        statement_date=datetime(2026, 6, 30, tzinfo=UTC),
        price=91.40,
        current_assets=450_000_000,
        current_liabilities=300_000_000,
        inventory=150_000_000,
        shareholders_equity=800_000_000,
        shares_outstanding=100_000_000,
        net_income=196_800_000,
        revenue=5_000_000_000,
        previous_year_revenue=4_200_000_000,
        operating_profit_after_tax=300_000_000,
        invested_capital=1_500_000_000,
        cash_from_operations=900_000_000,
        capex=250_000_000,
        dividend_per_share=3.75,
        eps=6.10,
        data_source="ng_research_agent",
        source_urls={"price": "https://example.com/gtco"},
    )

    assert await get_cached_fetch("NG", "GTCO", "cycle-1") is None

    await cache_fetch("NG", "GTCO", "cycle-1", result)
    cached = await get_cached_fetch("NG", "GTCO", "cycle-1")

    assert cached is not None
    assert cached.ticker == "GTCO"
    assert cached.statement_date == result.statement_date
    assert cached.price == 91.40
    assert cached.source_urls == {"price": "https://example.com/gtco"}

    # A different cycle id is a genuinely different cache entry, not
    # a coincidental collision.
    assert await get_cached_fetch("NG", "GTCO", "cycle-2") is None
