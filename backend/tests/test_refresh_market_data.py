import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.read_cache import get_data_version
from app.integrations.market_data.base import FetchedFinancials
from app.models.fundamentals import stock_fundamentals_current
from app.models.market_data import (
    scoring_weights,
    stock_prices_current,
    stock_scores_current,
    stocks,
)
from app.workers.tasks.refresh_market_data import SEED_TICKERS, refresh_market

# Three NG Financial Services names, deliberately spread across a real
# range so percentile ranking and bucket assignment have something
# genuine to differentiate, not three identical stocks.
_FAKE_FINANCIALS = {
    "GTCO": dict(
        current_assets=450e6,
        current_liabilities=300e6,
        inventory=0,
        shareholders_equity=800e6,
        shares_outstanding=100e6,
        net_income=196.8e6,
        revenue=5e9,
        previous_year_revenue=4.2e9,
        operating_profit_after_tax=300e6,
        invested_capital=1.5e9,
        cash_from_operations=900e6,
        capex=250e6,
        dividend_per_share=3.75,
        eps=6.10,
        price=91.40,
    ),
    "ZENITHBANK": dict(
        current_assets=380e6,
        current_liabilities=340e6,
        inventory=0,
        shareholders_equity=500e6,
        shares_outstanding=90e6,
        net_income=90.5e6,
        revenue=3.8e9,
        previous_year_revenue=3.7e9,
        operating_profit_after_tax=140e6,
        invested_capital=1.1e9,
        cash_from_operations=500e6,
        capex=200e6,
        dividend_per_share=2.70,
        eps=4.0,
        price=48.15,
    ),
    "ACCESSCORP": dict(
        current_assets=300e6,
        current_liabilities=310e6,
        inventory=0,
        shareholders_equity=350e6,
        shares_outstanding=120e6,
        net_income=45e6,
        revenue=2.5e9,
        previous_year_revenue=2.6e9,
        operating_profit_after_tax=70e6,
        invested_capital=900e6,
        cash_from_operations=200e6,
        capex=180e6,
        dividend_per_share=1.10,
        eps=1.9,
        price=24.60,
    ),
}


class FakeProvider:
    """Stands in for NGResearchAgent/AlphaVantageProvider so this test
    exercises the real orchestration logic, real Postgres writes, real
    scoring, without a live API key, per the same testable design as
    every other integration this session."""

    def __init__(self, financials: dict[str, dict]):
        self._financials = financials
        self.calls: list[str] = []

    async def fetch(self, ticker: str, company_name: str = "") -> FetchedFinancials:
        self.calls.append(ticker)
        if ticker == "SEPLAT":
            raise RuntimeError("simulated provider failure for one ticker")
        data = self._financials[ticker]
        return FetchedFinancials(
            ticker=ticker,
            statement_date=datetime(2026, 6, 30, tzinfo=UTC),
            data_source="ng_research_agent",
            source_urls={"price": f"https://example.com/{ticker.lower()}"},
            **data,
        )


async def _seed_active_weights(db_session):
    equal = 1.0
    await db_session.execute(
        scoring_weights.insert().values(
            version="test-v1",
            is_active=True,
            metric_weights={
                "liquidity": {"current_ratio": equal, "quick_ratio": equal},
                "equity": {"shareholders_equity": equal, "book_value": equal},
                "profitability": {"net_profit_margin": equal, "roe": equal, "roic": equal},
                "valuation_and_growth": {
                    "pe_ratio": equal,
                    "free_cash_flow": equal,
                    "revenue_growth_rate": equal,
                },
                "dividends": {"dividend_yield": equal},
            },
            category_weights={
                "liquidity": equal,
                "equity": equal,
                "profitability": equal,
                "valuation_and_growth": equal,
                "dividends": equal,
            },
        )
    )


async def test_refresh_market_writes_stocks_fundamentals_prices_and_scores(db_session):
    await _seed_active_weights(db_session)
    # SEED_TICKERS["NG"] has 7 tickers; this fixture only has fake data
    # for 3 of them (all Financial Services, so they're real sector
    # peers of each other). The rest fail with a KeyError inside the
    # fake provider, exactly like a real provider failure would, real
    # coverage of "continue past a single ticker's failure" with
    # multiple failures in the same cycle, not just one.
    other_ng_tickers = [t for t, _, _ in SEED_TICKERS["NG"] if t not in _FAKE_FINANCIALS]

    provider = FakeProvider(_FAKE_FINANCIALS)
    result = await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)

    assert sorted(result["failed"]) == sorted(other_ng_tickers)
    assert result["refreshed"] == 3

    # Stocks were actually upserted.
    stock_rows = (
        (await db_session.execute(select(stocks).where(stocks.c.market == "NG"))).mappings().all()
    )
    tickers_in_db = {row["ticker"] for row in stock_rows}
    assert {"GTCO", "ZENITHBANK", "ACCESSCORP"}.issubset(tickers_in_db)
    assert "SEPLAT" not in tickers_in_db  # the failed ticker never got this far

    gtco_id = next(row["id"] for row in stock_rows if row["ticker"] == "GTCO")

    fundamentals = (
        (
            await db_session.execute(
                select(stock_fundamentals_current).where(
                    stock_fundamentals_current.c.stock_id == gtco_id
                )
            )
        )
        .mappings()
        .first()
    )
    assert fundamentals is not None
    assert float(fundamentals["net_income"]) == 196.8e6
    assert fundamentals["data_source"] == "ng_research_agent"
    assert fundamentals["source_urls"] == {"price": "https://example.com/gtco"}

    price = (
        (
            await db_session.execute(
                select(stock_prices_current).where(stock_prices_current.c.stock_id == gtco_id)
            )
        )
        .mappings()
        .first()
    )
    assert float(price["price"]) == 91.40

    score = (
        (
            await db_session.execute(
                select(stock_scores_current).where(stock_scores_current.c.stock_id == gtco_id)
            )
        )
        .mappings()
        .first()
    )
    assert score is not None
    assert score["bucket"] in ("well", "potential", "under")
    assert score["weights_version"] == "test-v1"
    # GTCO is the strongest on every metric in this fixture, it should
    # land in the top bucket among these three peers.
    assert score["bucket"] == "well"

    # The cache-version bump actually happened.
    assert await get_data_version("NG") >= 1


async def test_refresh_market_uses_the_staging_cache_on_a_retry(db_session):
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    cycle_id = uuid.uuid4().hex
    failing_ticker_count = len(SEED_TICKERS["NG"]) - len(_FAKE_FINANCIALS)

    await refresh_market("NG", provider, db_session, cycle_id=cycle_id)
    calls_after_first_run = len(provider.calls)

    # Same cycle id again: every ticker that succeeded the first time
    # should be served from the staging cache, not fetched a second
    # time, per docs/backend-architecture/02.md. A ticker that failed
    # never reached cache_fetch() in the first place (the exception
    # happens before that call), so it's expected to retry, that's
    # not a cache miss, there was never anything to cache.
    await refresh_market("NG", provider, db_session, cycle_id=cycle_id)

    assert len(provider.calls) == calls_after_first_run + failing_ticker_count
