import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numeric import floatify
from app.core.read_cache import bump_data_version
from app.db.session import async_session_factory
from app.integrations.market_data.base import (
    FetchedFinancials,
    MarketDataProvider,
    ProviderNotConfiguredError,
)
from app.integrations.market_data.cache import cache_fetch, get_cached_fetch
from app.integrations.market_data.sanity_check import (
    FUNDAMENTAL_CHANGE_THRESHOLD,
    PRICE_CHANGE_THRESHOLD,
    is_suspicious_change,
)
from app.models.fundamentals import stock_fundamentals_current, stock_fundamentals_history
from app.models.market_data import (
    price_history,
    scoring_weights,
    stock_prices_current,
    stock_scores_current,
    stock_scores_history,
    stocks,
)
from app.services.scoring import (
    ScoringWeights,
    assign_buckets,
    compute_raw_metrics,
    compute_scores_for_group,
)
from app.workers.celery import celery_app

logger = logging.getLogger("app.refresh")

# A starting ticker universe, per docs/backend-architecture/03-phases.md's
# Sub-phase 3.2, deliberately small and explicit: real NG and US
# listed-company sourcing is a separate, future task, tracked in
# docs/open-items.md, not something either the phases doc or the
# product docs specified in enough detail to build against yet.
SEED_TICKERS: dict[str, list[tuple[str, str, str]]] = {
    "NG": [
        ("GTCO", "Guaranty Trust Holding Co", "Financial Services"),
        ("ZENITHBANK", "Zenith Bank", "Financial Services"),
        ("DANGCEM", "Dangote Cement", "Industrial Goods"),
        ("MTNN", "MTN Nigeria", "ICT"),
        ("BUACEMENT", "BUA Cement", "Industrial Goods"),
        ("ACCESSCORP", "Access Holdings", "Financial Services"),
        ("SEPLAT", "Seplat Energy", "Oil and Gas"),
    ],
    "US": [
        ("AAPL", "Apple Inc.", "Information Technology"),
        ("MSFT", "Microsoft Corporation", "Information Technology"),
    ],
}


async def _upsert_stock(
    db: AsyncSession, ticker: str, company_name: str, market: str, sector: str
) -> uuid.UUID:
    stmt = (
        pg_insert(stocks)
        .values(
            id=uuid.uuid4(), ticker=ticker, company_name=company_name, market=market, sector=sector
        )
        .on_conflict_do_update(
            index_elements=["ticker", "market"],
            set_={"company_name": company_name, "sector": sector},
        )
        .returning(stocks.c.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _previous_fundamentals(db: AsyncSession, stock_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        select(stock_fundamentals_current).where(stock_fundamentals_current.c.stock_id == stock_id)
    )
    row = result.mappings().first()
    return floatify(dict(row)) if row else None


async def _previous_price(db: AsyncSession, stock_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        select(stock_prices_current).where(stock_prices_current.c.stock_id == stock_id)
    )
    row = result.mappings().first()
    return floatify(dict(row)) if row else None


def _fundamentals_columns(fetched: FetchedFinancials) -> dict:
    return {
        "statement_date": fetched.statement_date,
        "current_assets": fetched.current_assets,
        "current_liabilities": fetched.current_liabilities,
        "inventory": fetched.inventory,
        "shareholders_equity": fetched.shareholders_equity,
        "shares_outstanding": fetched.shares_outstanding,
        "net_income": fetched.net_income,
        "revenue": fetched.revenue,
        "previous_year_revenue": fetched.previous_year_revenue,
        "operating_profit_after_tax": fetched.operating_profit_after_tax,
        "invested_capital": fetched.invested_capital,
        "cash_from_operations": fetched.cash_from_operations,
        "capex": fetched.capex,
        "dividend_per_share": fetched.dividend_per_share,
        "eps": fetched.eps,
        "data_source": fetched.data_source,
        "source_urls": fetched.source_urls,
    }


async def _write_fundamentals_and_price(
    db: AsyncSession, stock_id: uuid.UUID, fetched: FetchedFinancials, now: datetime
) -> None:
    previous_fundamentals = await _previous_fundamentals(db, stock_id)
    previous_price = await _previous_price(db, stock_id)

    fundamentals_cols = _fundamentals_columns(fetched)
    needs_review = False
    if previous_fundamentals:
        for field in ("net_income", "revenue", "shareholders_equity"):
            if is_suspicious_change(
                previous_fundamentals.get(field),
                fundamentals_cols.get(field),
                FUNDAMENTAL_CHANGE_THRESHOLD,
            ):
                needs_review = True
                break
    fundamentals_cols["needs_review"] = needs_review

    await db.execute(
        pg_insert(stock_fundamentals_current)
        .values(stock_id=stock_id, last_successful_refresh_at=now, **fundamentals_cols)
        .on_conflict_do_update(
            index_elements=["stock_id"],
            set_={**fundamentals_cols, "last_successful_refresh_at": now},
        )
    )
    await db.execute(
        stock_fundamentals_history.insert().values(
            id=uuid.uuid4(), stock_id=stock_id, recorded_at=now, **fundamentals_cols
        )
    )

    previous_close = previous_price["price"] if previous_price else None
    change_percent = (
        0.0
        if previous_close in (None, 0) or fetched.price is None
        else (float(fetched.price) - float(previous_close)) / float(previous_close) * 100
    )
    price_needs_review = previous_price is not None and is_suspicious_change(
        previous_close, fetched.price, PRICE_CHANGE_THRESHOLD
    )

    await db.execute(
        pg_insert(stock_prices_current)
        .values(
            stock_id=stock_id,
            price=fetched.price,
            change_percent=change_percent,
            data_source=fetched.data_source,
            needs_review=price_needs_review,
            last_successful_refresh_at=now,
        )
        .on_conflict_do_update(
            index_elements=["stock_id"],
            set_={
                "price": fetched.price,
                "change_percent": change_percent,
                "data_source": fetched.data_source,
                "needs_review": price_needs_review,
                "last_successful_refresh_at": now,
            },
        )
    )
    if fetched.price is not None:
        await db.execute(
            price_history.insert().values(
                id=uuid.uuid4(),
                stock_id=stock_id,
                open=fetched.price,
                high=fetched.price,
                low=fetched.price,
                close=fetched.price,
                recorded_at=now,
            )
        )


async def _fetch_with_cache(
    provider: MarketDataProvider, market: str, ticker: str, company_name: str, cycle_id: str
) -> FetchedFinancials:
    cached = await get_cached_fetch(market, ticker, cycle_id)
    if cached is not None:
        return cached
    result = await provider.fetch(ticker, company_name)
    await cache_fetch(market, ticker, cycle_id, result)
    return result


async def refresh_market(
    market: str, provider: MarketDataProvider, db: AsyncSession, cycle_id: str | None = None
) -> dict:
    """Fetches every seed ticker in `market`, continuing past a single
    ticker's failure rather than aborting the whole cycle, per
    docs/backend-architecture/03-phases.md's Sub-phase 3.2, then scores
    every stock that has enough data, per sector, per 01.md, and bumps
    the market's read-path cache version, per 02.md. `provider` and
    `db` are both injected, not created here: `provider` so this can
    be tested against a fake one without a live API key, `db` so a
    test can inject the same rolled-back-transaction session
    tests/conftest.py already uses everywhere else, real database
    round trips, nothing left over once the test ends."""
    cycle_id = cycle_id or uuid.uuid4().hex
    now = datetime.now(UTC)
    stock_ids_by_sector: dict[str, list[uuid.UUID]] = defaultdict(list)
    failed_tickers: list[str] = []

    for ticker, company_name, sector in SEED_TICKERS[market]:
        try:
            fetched = await _fetch_with_cache(provider, market, ticker, company_name, cycle_id)
            # A nested transaction (SAVEPOINT) per ticker, not the
            # whole session: "continue past a single ticker's
            # failure" only means something if one ticker's bad write
            # can be undone without also undoing every ticker that
            # already succeeded in this same cycle.
            async with db.begin_nested():
                stock_id = await _upsert_stock(db, ticker, company_name, market, sector)
                await _write_fundamentals_and_price(db, stock_id, fetched, now)
            stock_ids_by_sector[sector].append(stock_id)
        except ProviderNotConfiguredError:
            raise
        except Exception:
            logger.exception("refresh failed for ticker %s in %s", ticker, market)
            failed_tickers.append(ticker)

    await _score_market(db, market, stock_ids_by_sector, now)
    await bump_data_version(market)
    return {
        "market": market,
        "refreshed": sum(len(v) for v in stock_ids_by_sector.values()),
        "failed": failed_tickers,
    }


async def _score_market(
    db: AsyncSession, market: str, stock_ids_by_sector: dict[str, list[uuid.UUID]], now: datetime
) -> None:
    weights_row = await db.execute(
        select(scoring_weights).where(scoring_weights.c.is_active.is_(True))
    )
    weights_record = weights_row.mappings().first()
    if weights_record is None:
        logger.warning("no active scoring_weights row, skipping scoring for %s", market)
        return
    weights = ScoringWeights(
        version=weights_record["version"],
        metric_weights=weights_record["metric_weights"],
        category_weights=weights_record["category_weights"],
    )

    for stock_ids in stock_ids_by_sector.values():
        raw_metrics_by_stock: dict[str, dict] = {}
        for stock_id in stock_ids:
            fundamentals = await _previous_fundamentals(db, stock_id)
            price_row = await _previous_price(db, stock_id)
            if not fundamentals:
                continue
            price = (
                float(price_row["price"]) if price_row and price_row["price"] is not None else None
            )
            raw_metrics_by_stock[str(stock_id)] = compute_raw_metrics(fundamentals, price)

        if not raw_metrics_by_stock:
            continue

        results = compute_scores_for_group(raw_metrics_by_stock, weights)
        scorable = {
            sid: r.composite_score for sid, r in results.items() if r.composite_score is not None
        }
        buckets = assign_buckets(scorable)

        for sid_str, result in results.items():
            if result.composite_score is None:
                continue
            stock_id = uuid.UUID(sid_str)
            bucket = buckets[sid_str]
            values = {
                "composite_score": result.composite_score,
                "bucket": bucket,
                "metric_detail": result.metric_detail,
                "weights_version": weights.version,
                "computed_at": now,
            }
            await db.execute(
                pg_insert(stock_scores_current)
                .values(stock_id=stock_id, last_successful_refresh_at=now, **values)
                .on_conflict_do_update(
                    index_elements=["stock_id"],
                    set_={**values, "last_successful_refresh_at": now},
                )
            )
            await db.execute(
                stock_scores_history.insert().values(id=uuid.uuid4(), stock_id=stock_id, **values)
            )


async def _run_refresh(market: str, provider: MarketDataProvider) -> dict:
    async with async_session_factory() as db:
        result = await refresh_market(market, provider, db)
        await db.commit()
        return result


@celery_app.task(name="refresh_market_data")
def refresh_market_data_task(market: str) -> dict:
    from app.integrations.market_data.alpha_vantage import AlphaVantageProvider
    from app.integrations.market_data.ng_research_agent import NGResearchAgent

    provider = NGResearchAgent() if market == "NG" else AlphaVantageProvider()
    return asyncio.run(_run_refresh(market, provider))
