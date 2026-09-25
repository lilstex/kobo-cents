from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.numeric import floatify
from app.core.read_cache import get_cached_json, get_data_version, set_cached_json
from app.db.session import get_db
from app.models.fundamentals import stock_fundamentals_current
from app.models.market_data import stock_prices_current, stock_scores_current, stocks
from app.schemas.market import (
    CategoryBlock,
    CompareResponse,
    GlossaryPayloadEntry,
    MetricValue,
    OverviewResponse,
    SearchResponse,
    SearchResultItem,
    StockDetailResponse,
    StockSummary,
)
from app.services.explainability import explain
from app.services.glossary import METRIC_GLOSSARY
from app.services.scoring import (
    CATEGORIES,
    METRIC_DEFINITIONS,
    category_scores_from_metric_detail,
    compute_raw_metrics,
)

router = APIRouter(tags=["market"])

_VALID_MARKETS = {"NG", "US"}
_VALID_BUCKETS = {"well", "potential", "under"}


def _validate_market(market: str) -> str:
    market = market.upper()
    if market not in _VALID_MARKETS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown market: {market}")
    return market


@router.get("/markets/{market}/overview", response_model=OverviewResponse)
async def market_overview(
    market: str,
    sector: str | None = Query(default=None),
    bucket: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> OverviewResponse:
    """Bucket and sector filtered, offset-paginated, cache-aside
    against Redis with the versioned key pattern from
    docs/backend-architecture/02.md: a miss falls back to Postgres,
    already fast given the indexing in 01.md, then populates the
    cache. Only already-scored stocks show up here, per 01.md's
    "market overview reads already-computed rows" rule, no scoring
    happens on this request path."""
    market = _validate_market(market)
    if bucket is not None and bucket not in _VALID_BUCKETS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown bucket: {bucket}")

    version = await get_data_version(market)
    cache_key = f"overview:{market}:{sector or 'all'}:{bucket or 'all'}:{limit}:{offset}:v{version}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return OverviewResponse(**cached)

    base = stocks.join(stock_scores_current, stock_scores_current.c.stock_id == stocks.c.id).join(
        stock_prices_current, stock_prices_current.c.stock_id == stocks.c.id, isouter=True
    )
    where_clauses = [stocks.c.market == market]
    if sector:
        where_clauses.append(stocks.c.sector == sector)
    if bucket:
        where_clauses.append(stock_scores_current.c.bucket == bucket)

    count_result = await db.execute(select(func.count()).select_from(base).where(*where_clauses))
    total = count_result.scalar_one()

    rows_result = await db.execute(
        select(
            stocks.c.ticker,
            stocks.c.company_name,
            stocks.c.market,
            stocks.c.sector,
            stock_prices_current.c.price,
            stock_prices_current.c.change_percent,
            stock_scores_current.c.composite_score,
            stock_scores_current.c.bucket,
            stock_scores_current.c.last_successful_refresh_at,
        )
        .select_from(base)
        .where(*where_clauses)
        .order_by(stock_scores_current.c.composite_score.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [StockSummary(**floatify(dict(row))) for row in rows_result.mappings().all()]
    response = OverviewResponse(items=items, total=total, limit=limit, offset=offset)
    await set_cached_json(cache_key, response.model_dump(mode="json"))
    return response


async def _load_stock_detail(db: AsyncSession, stock: dict) -> StockDetailResponse:
    """The actual read-and-assemble work behind a stock detail
    response, shared by the detail endpoint and compare, per 02.md's
    explicit note that compare should reuse individual stock detail
    reads rather than growing its own cache. Cache-aside is the
    caller's job (different cache key shape for a single stock versus
    a comparison), this function always does the real read."""
    stock_id = stock["id"]

    scores_result = await db.execute(
        select(stock_scores_current).where(stock_scores_current.c.stock_id == stock_id)
    )
    scores_row = scores_result.mappings().first()

    fundamentals_result = await db.execute(
        select(stock_fundamentals_current).where(stock_fundamentals_current.c.stock_id == stock_id)
    )
    fundamentals_row = fundamentals_result.mappings().first()

    price_result = await db.execute(
        select(stock_prices_current).where(stock_prices_current.c.stock_id == stock_id)
    )
    price_row = price_result.mappings().first()

    fundamentals = floatify(dict(fundamentals_row)) if fundamentals_row else {}
    price = float(price_row["price"]) if price_row and price_row["price"] is not None else None
    raw_metrics = compute_raw_metrics(fundamentals, price)

    metric_detail: dict = scores_row["metric_detail"] if scores_row else {}
    category_scores = category_scores_from_metric_detail(metric_detail)

    categories = [
        CategoryBlock(
            category=category,
            score=category_scores.get(category),
            metrics=[
                MetricValue(
                    key=metric_def.key,
                    label=METRIC_GLOSSARY[metric_def.key].term,
                    value=raw_metrics.get(metric_def.key),
                    percentile=metric_detail.get(metric_def.key, {}).get("percentile"),
                )
                for metric_def in METRIC_DEFINITIONS
                if metric_def.category == category
            ],
        )
        for category in CATEGORIES
    ]

    return StockDetailResponse(
        ticker=stock["ticker"],
        company_name=stock["company_name"],
        market=stock["market"],
        sector=stock["sector"],
        price=price,
        change_percent=(
            float(price_row["change_percent"])
            if price_row and price_row["change_percent"] is not None
            else None
        ),
        composite_score=float(scores_row["composite_score"]) if scores_row else None,
        bucket=scores_row["bucket"] if scores_row else None,
        categories=categories,
        explanation=explain(metric_detail, scores_row["bucket"] if scores_row else ""),
        glossary={
            key: GlossaryPayloadEntry(
                term=entry.term, short_definition=entry.short_definition, slug=entry.slug
            )
            for key, entry in METRIC_GLOSSARY.items()
        },
        news=[],
        scores_as_of=scores_row["last_successful_refresh_at"] if scores_row else None,
        price_as_of=price_row["last_successful_refresh_at"] if price_row else None,
        fundamentals_as_of=(
            fundamentals_row["last_successful_refresh_at"] if fundamentals_row else None
        ),
    )


async def _resolve_stock(db: AsyncSession, ticker: str, market: str | None) -> dict:
    ticker = ticker.upper()
    where_clauses = [stocks.c.ticker == ticker]
    if market:
        where_clauses.append(stocks.c.market == _validate_market(market))
    result = await db.execute(select(stocks).where(*where_clauses))
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No stock found for ticker {ticker}")
    if len(rows) > 1:
        # The same ticker string exists in both markets, a real if
        # rare possibility the schema explicitly allows (unique on
        # (ticker, market), not ticker alone). Ask for the market
        # rather than silently guessing which one was meant.
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Ticker {ticker} exists in more than one market, pass ?market= to disambiguate",
        )
    return dict(rows[0])


@router.get("/stocks/{ticker}", response_model=StockDetailResponse)
async def stock_detail(
    ticker: str,
    market: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> StockDetailResponse:
    stock = await _resolve_stock(db, ticker, market)
    version = await get_data_version(stock["market"])
    cache_key = f"stock:{stock['market']}:{stock['ticker']}:v{version}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return StockDetailResponse(**cached)

    response = await _load_stock_detail(db, stock)
    await set_cached_json(cache_key, response.model_dump(mode="json"))
    return response


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=1),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> SearchResponse:
    """Typo-tolerant trigram search over ticker and company name, per
    01.md: "zenit" still finds Zenith Bank. Ranked by whichever of the
    two columns matches better, not summed, so a strong ticker match
    doesn't get out-ranked by a weak name match added on top of it."""
    similarity = func.greatest(
        func.similarity(stocks.c.ticker, q), func.similarity(stocks.c.company_name, q)
    )
    result = await db.execute(
        select(stocks)
        .where(stocks.c.listing_status == "active", similarity > 0.1)
        .order_by(similarity.desc())
        .limit(20)
    )
    items = [
        SearchResultItem(
            ticker=row["ticker"],
            company_name=row["company_name"],
            market=row["market"],
            sector=row["sector"],
        )
        for row in result.mappings().all()
    ]
    return SearchResponse(items=items)


@router.get("/compare", response_model=CompareResponse)
async def compare(
    tickers: str = Query(description="Comma-separated tickers, 2 or 3"),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> CompareResponse:
    """No new storage, per 01.md: fetches each stock's already-cached
    detail read and computes the best-in-comparison highlight at
    render time. Best is judged by percentile, the same number
    already shown on the page for each metric, since the scoring
    pipeline itself has no separate notion of a metric's "good"
    direction beyond a higher sector-relative percentile."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not (2 <= len(ticker_list) <= 3):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pass 2 or 3 comma-separated tickers")

    details = []
    for ticker in ticker_list:
        stock = await _resolve_stock(db, ticker, None)
        version = await get_data_version(stock["market"])
        cache_key = f"stock:{stock['market']}:{stock['ticker']}:v{version}"
        cached = await get_cached_json(cache_key)
        if cached is not None:
            details.append(StockDetailResponse(**cached))
            continue
        detail = await _load_stock_detail(db, stock)
        await set_cached_json(cache_key, detail.model_dump(mode="json"))
        details.append(detail)

    best_in_comparison: dict[str, str] = {}
    for metric_def in METRIC_DEFINITIONS:
        best_ticker, best_percentile = None, None
        for detail in details:
            for category in detail.categories:
                if category.category != metric_def.category:
                    continue
                for metric in category.metrics:
                    if metric.key != metric_def.key or metric.percentile is None:
                        continue
                    if best_percentile is None or metric.percentile > best_percentile:
                        best_ticker, best_percentile = detail.ticker, metric.percentile
        if best_ticker is not None:
            best_in_comparison[metric_def.key] = best_ticker

    return CompareResponse(stocks=details, best_in_comparison=best_in_comparison)
