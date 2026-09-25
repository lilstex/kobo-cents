from app.services.scoring import (
    ScoringWeights,
    assign_buckets,
    compute_raw_metrics,
    compute_scores_for_group,
    percentile_ranks,
)


def test_compute_raw_metrics_matches_hand_worked_formulas():
    fundamentals = {
        "current_assets": 450_000_000,
        "current_liabilities": 300_000_000,
        "inventory": 150_000_000,
        "shareholders_equity": 800_000_000,
        "shares_outstanding": 100_000_000,
        "net_income": 196_800_000,
        "revenue": 5_000_000_000,
        "previous_year_revenue": 4_200_000_000,
        "operating_profit_after_tax": 300_000_000,
        "invested_capital": 1_500_000_000,
        "cash_from_operations": 900_000_000,
        "capex": 250_000_000,
        "dividend_per_share": 3.75,
        "eps": 6.10,
    }
    metrics = compute_raw_metrics(fundamentals, price=91.40)

    assert metrics["current_ratio"] == 450_000_000 / 300_000_000
    assert metrics["quick_ratio"] == (450_000_000 - 150_000_000) / 300_000_000
    assert metrics["shareholders_equity"] == 800_000_000
    assert metrics["book_value"] == 8.0
    assert metrics["net_profit_margin"] == 196_800_000 / 5_000_000_000
    assert metrics["roe"] == 196_800_000 / 800_000_000
    assert metrics["roic"] == 300_000_000 / 1_500_000_000
    assert round(metrics["pe_ratio"], 2) == round(91.40 / 6.10, 2)
    assert metrics["free_cash_flow"] == 650_000_000
    assert round(metrics["revenue_growth_rate"], 4) == round(800_000_000 / 4_200_000_000, 4)
    assert round(metrics["dividend_yield"], 4) == round(3.75 / 91.40, 4)


def test_compute_raw_metrics_missing_dividend_is_none_not_zero():
    """A non-dividend-paying growth stock, per docs/01_product.md's
    explicit reasoning: a missing input produces a missing metric,
    never a value that scores as if the company failed at it."""
    fundamentals = {"dividend_per_share": None}
    metrics = compute_raw_metrics(fundamentals, price=100.0)
    assert metrics["dividend_yield"] is None


def test_compute_raw_metrics_never_divides_by_zero():
    fundamentals = {"current_assets": 100, "current_liabilities": 0}
    metrics = compute_raw_metrics(fundamentals, price=None)
    assert metrics["current_ratio"] is None
    assert metrics["pe_ratio"] is None


def test_percentile_ranks_matches_postgres_percent_rank_semantics():
    # Four distinct values: percentile ranks should be 0, 1/3, 2/3, 1
    values = {"a": 10.0, "b": 20.0, "c": 30.0, "d": 40.0}
    ranks = percentile_ranks(values)
    assert ranks["a"] == 0.0
    assert round(ranks["b"], 4) == round(100 / 3, 4)
    assert round(ranks["c"], 4) == round(200 / 3, 4)
    assert ranks["d"] == 100.0


def test_percentile_ranks_averages_ties():
    values = {"a": 10.0, "b": 10.0, "c": 30.0}
    ranks = percentile_ranks(values)
    # a and b tie for rank 0 and 1 (0-indexed), average rank 0.5
    assert ranks["a"] == ranks["b"] == 25.0
    assert ranks["c"] == 100.0


def test_percentile_ranks_single_stock_sector_gets_50():
    assert percentile_ranks({"only": 42.0}) == {"only": 50.0}


def _weights():
    return ScoringWeights(
        version="v1",
        metric_weights={
            "liquidity": {"current_ratio": 1.0, "quick_ratio": 1.0},
            "equity": {"shareholders_equity": 1.0, "book_value": 1.0},
            "profitability": {"net_profit_margin": 1.0, "roe": 1.0, "roic": 1.0},
            "valuation_and_growth": {
                "pe_ratio": 1.0,
                "free_cash_flow": 1.0,
                "revenue_growth_rate": 1.0,
            },
            "dividends": {"dividend_yield": 1.0},
        },
        category_weights={
            "liquidity": 1.0,
            "equity": 1.0,
            "profitability": 1.0,
            "valuation_and_growth": 1.0,
            "dividends": 1.0,
        },
    )


def test_missing_metric_is_excluded_and_remaining_weights_renormalized():
    """The stock detail worked example from docs/backend-architecture/
    01.md: a non-dividend payer isn't scored as if it failed on
    dividends, the dividends category is simply excluded from its
    composite rather than dragging it down."""
    stocks = {
        "payer": {
            "dividend_yield": 5.0,
            **{
                m: 50.0
                for m in [
                    "current_ratio",
                    "quick_ratio",
                    "shareholders_equity",
                    "book_value",
                    "net_profit_margin",
                    "roe",
                    "roic",
                    "pe_ratio",
                    "free_cash_flow",
                    "revenue_growth_rate",
                ]
            },
        },
        "non_payer": {
            "dividend_yield": None,
            **{
                m: 50.0
                for m in [
                    "current_ratio",
                    "quick_ratio",
                    "shareholders_equity",
                    "book_value",
                    "net_profit_margin",
                    "roe",
                    "roic",
                    "pe_ratio",
                    "free_cash_flow",
                    "revenue_growth_rate",
                ]
            },
        },
    }
    results = compute_scores_for_group(stocks, _weights())

    # Both stocks are identical on every other metric (all 50th
    # percentile against each other, since both are 50.0 for every
    # shared metric). non_payer's dividends category is None
    # (excluded), not 0, so its composite isn't dragged down relative
    # to what it would be with a genuinely bad dividend showing.
    assert results["non_payer"].metric_detail.get("dividend_yield") is None
    assert results["non_payer"].composite_score is not None
    # payer and non_payer end up with the same composite score here:
    # every metric they share is identical (50 vs 50 has no
    # percentile spread since it's a two-stock tie), and the one
    # metric that differs is excluded entirely for non_payer rather
    # than counted against it.
    assert results["payer"].composite_score == results["non_payer"].composite_score


def test_assign_buckets_splits_into_three_tiers_by_rank():
    scores = {f"s{i}": float(i) for i in range(9)}  # 0..8, higher is better
    buckets = assign_buckets(scores)
    well = [sid for sid, b in buckets.items() if b == "well"]
    potential = [sid for sid, b in buckets.items() if b == "potential"]
    under = [sid for sid, b in buckets.items() if b == "under"]

    assert set(well) == {"s8", "s7", "s6"}
    assert set(potential) == {"s5", "s4", "s3"}
    assert set(under) == {"s2", "s1", "s0"}
