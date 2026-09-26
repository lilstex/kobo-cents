from app.services.explainability import explain, select_outliers


def _detail(**percentiles):
    return {key: {"percentile": pct, "weight": 1.0} for key, pct in percentiles.items()}


def test_select_outliers_picks_the_furthest_from_median_both_directions():
    detail = _detail(
        roe=90.0,  # strong positive outlier
        revenue_growth_rate=10.0,  # strong negative outlier
        current_ratio=52.0,  # close to median, not an outlier
        dividend_yield=55.0,  # close to median, not an outlier
    )
    outliers = select_outliers(detail, top_k=3)
    keys = [o.metric_key for o in outliers]
    assert "roe" in keys
    assert "revenue_growth_rate" in keys
    assert "current_ratio" not in keys  # crowded out by stronger outliers


def test_explain_names_both_a_strength_and_a_weakness():
    detail = _detail(roe=92.0, revenue_growth_rate=8.0)
    sentence = explain(detail, bucket="potential")
    assert "ROE" in sentence
    assert "revenue growth" in sentence
    assert "showing potential" in sentence


def test_explain_handles_no_metrics_gracefully():
    assert "Not enough data" in explain({}, bucket="potential")


def test_explain_is_deterministic():
    detail = _detail(roe=95.0, roic=90.0, net_profit_margin=15.0)
    assert explain(detail, bucket="well") == explain(detail, bucket="well")
