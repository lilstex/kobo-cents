from datetime import datetime

from pydantic import BaseModel


class StockSummary(BaseModel):
    ticker: str
    company_name: str
    market: str
    sector: str
    price: float | None
    change_percent: float | None
    composite_score: float | None
    bucket: str | None
    last_successful_refresh_at: datetime | None


class OverviewResponse(BaseModel):
    items: list[StockSummary]
    total: int
    limit: int
    offset: int


class MetricValue(BaseModel):
    key: str
    label: str
    value: float | None
    percentile: float | None


class CategoryBlock(BaseModel):
    category: str
    score: float | None
    metrics: list[MetricValue]


class GlossaryPayloadEntry(BaseModel):
    term: str
    short_definition: str
    slug: str


class StockDetailResponse(BaseModel):
    ticker: str
    company_name: str
    market: str
    sector: str
    price: float | None
    change_percent: float | None
    composite_score: float | None
    bucket: str | None
    categories: list[CategoryBlock]
    explanation: str
    glossary: dict[str, GlossaryPayloadEntry]
    # Linked out, never republished, per 01_product.md. Empty until a
    # news source is actually wired up, a real, tracked gap, see
    # docs/open-items.md, not an oversight.
    news: list[dict]
    scores_as_of: datetime | None
    price_as_of: datetime | None
    fundamentals_as_of: datetime | None


class PricePoint(BaseModel):
    recorded_at: datetime
    price: float


class PriceHistoryResponse(BaseModel):
    items: list[PricePoint]


class SearchResultItem(BaseModel):
    ticker: str
    company_name: str
    market: str
    sector: str


class SearchResponse(BaseModel):
    items: list[SearchResultItem]


class CompareResponse(BaseModel):
    stocks: list[StockDetailResponse]
    # metric_key -> ticker of whichever compared stock has the
    # highest percentile for that metric, per 01.md: a render-time
    # max pass, nothing persisted, meaningful only for this specific
    # set of tickers.
    best_in_comparison: dict[str, str]
