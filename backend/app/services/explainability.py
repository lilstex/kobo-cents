from dataclasses import dataclass

# Metric names in plain language, for template sentences. Not the same
# as the glossary content on the frontend, this is the short phrase
# that fits mid-sentence ("ROE is strong"), the frontend's glossary
# owns the full explanation.
_METRIC_PHRASES = {
    "current_ratio": "current ratio",
    "quick_ratio": "quick ratio",
    "shareholders_equity": "shareholders' equity",
    "book_value": "book value",
    "net_profit_margin": "net profit margin",
    "roe": "ROE",
    "roic": "ROIC",
    "pe_ratio": "P/E ratio",
    "free_cash_flow": "free cash flow",
    "revenue_growth_rate": "revenue growth",
    "dividend_yield": "dividend yield",
}

_TOP_K = 3
_SECTOR_MEDIAN = 50.0


@dataclass
class Outlier:
    metric_key: str
    percentile: float
    distance_from_median: float
    direction: str  # "positive" | "negative"


def select_outliers(metric_detail: dict, top_k: int = _TOP_K) -> list[Outlier]:
    """Top-k selection over percentiles docs/backend-architecture/
    01.md already computed during scoring, not a new calculation: rank
    every metric by how far it sits from the sector median, in either
    direction, and take the strongest few. Deterministic, and
    guaranteed to match the numbers on the same page, since it's built
    from the same numbers."""
    outliers = [
        Outlier(
            metric_key=key,
            percentile=detail["percentile"],
            distance_from_median=abs(detail["percentile"] - _SECTOR_MEDIAN),
            direction="positive" if detail["percentile"] >= _SECTOR_MEDIAN else "negative",
        )
        for key, detail in metric_detail.items()
    ]
    outliers.sort(key=lambda o: o.distance_from_median, reverse=True)
    return outliers[:top_k]


def explain(metric_detail: dict, bucket: str) -> str:
    """Template sentences, not a live model call, per 01.md: instant,
    free to run at read time, and guaranteed to actually match the
    metrics on the page since it's built from the same top-k list."""
    outliers = select_outliers(metric_detail)
    if not outliers:
        return "Not enough data yet to explain this stock's score."

    positives = [o for o in outliers if o.direction == "positive"]
    negatives = [o for o in outliers if o.direction == "negative"]

    def phrase(outlier: Outlier) -> str:
        return _METRIC_PHRASES.get(outlier.metric_key, outlier.metric_key)

    parts = []
    if positives:
        parts.append(
            " and ".join(phrase(o) for o in positives)
            + (" are strong" if len(positives) > 1 else " is strong")
        )
    if negatives:
        parts.append(
            " and ".join(phrase(o) for o in negatives)
            + (
                " are weaker than sector peers"
                if len(negatives) > 1
                else " is weaker than sector peers"
            )
        )

    reasoning = ", but ".join(parts) if len(parts) > 1 else parts[0]
    bucket_labels = {
        "well": "performing well",
        "potential": "showing potential",
        "under": "underperforming",
    }
    label = bucket_labels.get(bucket, bucket)
    return f"{reasoning}, that combination is why this stock is {label}."
