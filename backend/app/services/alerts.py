# Alert matching, per docs/backend-architecture/01.md's "diff changed
# stocks" design and docs/01_product.md's "notify a user when a
# favorited stock's score changes, or crosses a price threshold they
# set." Kept pure and DB-independent, same separation as
# app/services/scoring.py and explainability.py: the refresh job (app/
# workers/tasks/refresh_market_data.py) does the database reads and
# the Celery dispatch, this module only ever decides yes/no given
# plain values, fully unit-testable without a database.

# Gates the coarse "did this stock move enough to even bother checking
# its alerts" filter, the O(changed) optimization 01.md describes,
# not any individual alert's own condition, that's alert_fires below.
# A deliberately chosen starting value on the 0-100 composite score
# scale, not derived from real usage data yet, flagged in
# docs/open-items.md as worth tuning once there is some.
COMPOSITE_SCORE_CHANGE_THRESHOLD = 3.0


def stock_changed_enough_to_check_alerts(
    previous_composite_score: float | None,
    new_composite_score: float | None,
    previous_price: float | None,
    new_price: float | None,
) -> bool:
    """Bounds the real work to stocks that actually moved, per 01.md,
    rather than checking every alert against every stock every cycle.
    A stock being scored for the first time has nothing to have
    "changed" from yet, so it never passes this filter, its alerts (if
    any exist, which they can't until it's favorited and has a first
    score) simply wait for the next cycle's real comparison."""
    if previous_composite_score is None or new_composite_score is None:
        return False
    score_moved = (
        abs(new_composite_score - previous_composite_score) >= COMPOSITE_SCORE_CHANGE_THRESHOLD
    )
    price_moved = (
        previous_price is not None and new_price is not None and previous_price != new_price
    )
    return score_moved or price_moved


def alert_fires(
    rule_type: str,
    rule_config: dict,
    previous_bucket: str | None,
    new_bucket: str | None,
    previous_price: float | None,
    new_price: float | None,
) -> bool:
    """Score-change alerts fire on an actual bucket transition
    (well/potential/under), the classification a user actually sees
    on the market overview, not a raw composite-score-point move they
    never see directly. Price-threshold alerts fire only on the cycle
    the price actually crosses the configured level (previous side,
    new side), not on every subsequent cycle it happens to still sit
    past it, so a stock parked above a threshold for weeks doesn't
    re-notify every single refresh."""
    if rule_type == "score_change":
        return (
            previous_bucket is not None and new_bucket is not None and previous_bucket != new_bucket
        )
    if rule_type == "price_threshold":
        if previous_price is None or new_price is None:
            return False
        direction = rule_config.get("direction")
        threshold = rule_config.get("price")
        if threshold is None:
            return False
        if direction == "above":
            return previous_price < threshold <= new_price
        if direction == "below":
            return previous_price > threshold >= new_price
        return False
    return False
