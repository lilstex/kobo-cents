from dataclasses import dataclass, field

# The eleven metrics from docs/01_product.md, grouped into the same
# five categories used on the stock detail page, per
# docs/backend-architecture/01.md. Every metric, including the two raw
# equity figures, gets ranked as a sector-relative percentile, never
# judged against a fixed number, per that same document's reasoning.

CATEGORIES = ["liquidity", "equity", "profitability", "valuation_and_growth", "dividends"]


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    category: str


METRIC_DEFINITIONS: list[MetricDefinition] = [
    MetricDefinition("current_ratio", "liquidity"),
    MetricDefinition("quick_ratio", "liquidity"),
    MetricDefinition("shareholders_equity", "equity"),
    MetricDefinition("book_value", "equity"),
    MetricDefinition("net_profit_margin", "profitability"),
    MetricDefinition("roe", "profitability"),
    MetricDefinition("roic", "profitability"),
    MetricDefinition("pe_ratio", "valuation_and_growth"),
    MetricDefinition("free_cash_flow", "valuation_and_growth"),
    MetricDefinition("revenue_growth_rate", "valuation_and_growth"),
    MetricDefinition("dividend_yield", "dividends"),
]


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def compute_raw_metrics(fundamentals: dict, price: float | None) -> dict[str, float | None]:
    """Turns the raw figures in stock_fundamentals_current/history plus
    the current price into the eleven metric values, per the formulas
    named in docs/01_product.md. A missing input produces a missing
    metric (None), never a zero, so it gets excluded and its weight
    renormalized downstream rather than silently penalized."""
    current_assets = fundamentals.get("current_assets")
    inventory = fundamentals.get("inventory")
    quick_assets = (
        None if current_assets is None or inventory is None else current_assets - inventory
    )
    cash_from_operations = fundamentals.get("cash_from_operations")
    capex = fundamentals.get("capex")
    free_cash_flow = (
        None if cash_from_operations is None or capex is None else cash_from_operations - capex
    )
    revenue = fundamentals.get("revenue")
    previous_year_revenue = fundamentals.get("previous_year_revenue")
    revenue_change = (
        None
        if revenue is None or previous_year_revenue is None
        else revenue - previous_year_revenue
    )

    return {
        "current_ratio": _safe_div(current_assets, fundamentals.get("current_liabilities")),
        "quick_ratio": _safe_div(quick_assets, fundamentals.get("current_liabilities")),
        "shareholders_equity": fundamentals.get("shareholders_equity"),
        "book_value": _safe_div(
            fundamentals.get("shareholders_equity"), fundamentals.get("shares_outstanding")
        ),
        "net_profit_margin": _safe_div(fundamentals.get("net_income"), revenue),
        "roe": _safe_div(fundamentals.get("net_income"), fundamentals.get("shareholders_equity")),
        "roic": _safe_div(
            fundamentals.get("operating_profit_after_tax"), fundamentals.get("invested_capital")
        ),
        "pe_ratio": _safe_div(price, fundamentals.get("eps")),
        "free_cash_flow": free_cash_flow,
        "revenue_growth_rate": _safe_div(revenue_change, previous_year_revenue),
        "dividend_yield": _safe_div(fundamentals.get("dividend_per_share"), price),
    }


def percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    """Sector-relative percentile rank per docs/backend-architecture/
    01.md, matching Postgres's PERCENT_RANK() semantics: (rank - 1) /
    (n - 1) * 100, ties given the average rank of their group. A
    single-stock group (a genuinely small sector) gets 50, the only
    value that means anything when there's no peer to rank against."""
    n = len(values)
    if n == 0:
        return {}
    if n == 1:
        return dict.fromkeys(values, 50.0)

    sorted_items = sorted(values.items(), key=lambda kv: kv[1])
    ranks: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_items[j + 1][1] == sorted_items[i][1]:
            j += 1
        avg_rank = (i + j) / 2
        for k in range(i, j + 1):
            stock_id = sorted_items[k][0]
            ranks[stock_id] = avg_rank / (n - 1) * 100
        i = j + 1
    return ranks


@dataclass
class ScoringWeights:
    version: str
    metric_weights: dict[str, dict[str, float]]  # category -> metric_key -> weight
    category_weights: dict[str, float]  # category -> weight


@dataclass
class ScoreResult:
    composite_score: float | None
    bucket: str | None
    metric_detail: dict = field(default_factory=dict)


def compute_scores_for_group(
    stocks_raw_metrics: dict[str, dict[str, float | None]],
    weights: ScoringWeights,
) -> dict[str, ScoreResult]:
    """One sector-and-market group at a time, per 01.md: percentile
    ranking only ever compares a stock against its own sector peers.
    Missing metrics are excluded from their category's weighted
    average and the remaining weights renormalized, never scored as
    zero, per 01.md's explicit reasoning against penalizing, for
    instance, a non-dividend-paying growth stock."""
    metric_percentiles: dict[str, dict[str, float]] = {}
    for metric_def in METRIC_DEFINITIONS:
        values = {
            stock_id: metrics[metric_def.key]
            for stock_id, metrics in stocks_raw_metrics.items()
            if metrics.get(metric_def.key) is not None
        }
        metric_percentiles[metric_def.key] = percentile_ranks(values)

    results: dict[str, ScoreResult] = {}
    for stock_id in stocks_raw_metrics:
        metric_detail: dict = {}
        category_scores: dict[str, float | None] = {}

        for category in CATEGORIES:
            metrics_in_category = [m for m in METRIC_DEFINITIONS if m.category == category]
            weighted_sum, weight_total = 0.0, 0.0
            for metric_def in metrics_in_category:
                pctl = metric_percentiles[metric_def.key].get(stock_id)
                if pctl is None:
                    continue
                weight = weights.metric_weights.get(category, {}).get(metric_def.key, 0.0)
                weighted_sum += pctl * weight
                weight_total += weight
                metric_detail[metric_def.key] = {"percentile": round(pctl, 2), "weight": weight}
            category_scores[category] = (weighted_sum / weight_total) if weight_total > 0 else None

        comp_weighted_sum, comp_weight_total = 0.0, 0.0
        for category, score in category_scores.items():
            if score is None:
                continue
            weight = weights.category_weights.get(category, 0.0)
            comp_weighted_sum += score * weight
            comp_weight_total += weight
        composite = (comp_weighted_sum / comp_weight_total) if comp_weight_total > 0 else None

        results[stock_id] = ScoreResult(
            composite_score=round(composite, 4) if composite is not None else None,
            bucket=None,
            metric_detail=metric_detail,
        )
    return results


def category_scores_from_metric_detail(metric_detail: dict) -> dict[str, float | None]:
    """The stock detail page groups metrics into the five categories
    from 01_product.md and shows a per-category score alongside them.
    That's a weighted average over percentiles already computed at
    refresh time, an O(1) read-time pass over one stock's own already-
    stored metric_detail, not the sector-wide percentile ranking 01.md
    reserves for refresh time. Mirrors the category step inside
    compute_scores_for_group exactly, just factored out so the API
    layer can call it without recomputing scores for the whole sector."""
    scores: dict[str, float | None] = {}
    for category in CATEGORIES:
        metrics_in_category = [m for m in METRIC_DEFINITIONS if m.category == category]
        weighted_sum, weight_total = 0.0, 0.0
        for metric_def in metrics_in_category:
            detail = metric_detail.get(metric_def.key)
            if detail is None:
                continue
            weighted_sum += detail["percentile"] * detail["weight"]
            weight_total += detail["weight"]
        scores[category] = round(weighted_sum / weight_total, 2) if weight_total > 0 else None
    return scores


def assign_buckets(composite_scores: dict[str, float]) -> dict[str, str]:
    """NTILE(3) by composite score within the group, per 01.md: the
    top third is "well", the middle "potential", the bottom "under",
    self-correcting cutoffs instead of a fixed score threshold."""
    ranked = sorted(composite_scores.items(), key=lambda kv: kv[1], reverse=True)
    n = len(ranked)
    labels = ["well", "potential", "under"]
    buckets: dict[str, str] = {}
    for i, (stock_id, _score) in enumerate(ranked):
        tier = min(i * 3 // n, 2)
        buckets[stock_id] = labels[tier]
    return buckets
