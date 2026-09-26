from app.services.alerts import (
    COMPOSITE_SCORE_CHANGE_THRESHOLD,
    alert_fires,
    stock_changed_enough_to_check_alerts,
)


def test_stock_not_changed_enough_when_first_ever_score():
    assert stock_changed_enough_to_check_alerts(None, 60.0, 91.4, 91.4) is False


def test_stock_not_changed_enough_when_score_and_price_both_stable():
    assert stock_changed_enough_to_check_alerts(60.0, 60.5, 91.4, 91.4) is False


def test_stock_changed_enough_when_score_moves_past_the_threshold():
    assert (
        stock_changed_enough_to_check_alerts(
            60.0, 60.0 + COMPOSITE_SCORE_CHANGE_THRESHOLD, 91.4, 91.4
        )
        is True
    )


def test_stock_changed_enough_when_price_moves_at_all_even_with_a_stable_score():
    assert stock_changed_enough_to_check_alerts(60.0, 60.0, 91.4, 92.0) is True


def test_score_change_alert_fires_on_a_bucket_transition():
    assert alert_fires("score_change", {}, "potential", "well", 91.4, 91.4) is True


def test_score_change_alert_does_not_fire_without_a_bucket_transition():
    assert alert_fires("score_change", {}, "well", "well", 91.4, 91.4) is False


def test_score_change_alert_does_not_fire_on_a_stock_never_scored_before():
    assert alert_fires("score_change", {}, None, "well", 91.4, 91.4) is False


def test_price_threshold_alert_fires_when_crossing_above():
    config = {"direction": "above", "price": 100.0}
    assert alert_fires("price_threshold", config, None, None, 98.0, 101.0) is True


def test_price_threshold_alert_does_not_fire_when_already_above_last_cycle():
    # Already past the threshold before this cycle even started: this
    # is the "don't re-notify every cycle it happens to sit above"
    # case, per app/services/alerts.py's own reasoning.
    config = {"direction": "above", "price": 100.0}
    assert alert_fires("price_threshold", config, None, None, 101.0, 102.0) is False


def test_price_threshold_alert_fires_when_crossing_below():
    config = {"direction": "below", "price": 50.0}
    assert alert_fires("price_threshold", config, None, None, 51.0, 49.0) is True


def test_price_threshold_alert_requires_both_prices():
    config = {"direction": "above", "price": 100.0}
    assert alert_fires("price_threshold", config, None, None, None, 101.0) is False


def test_unknown_rule_type_never_fires():
    assert alert_fires("mystery", {}, "potential", "well", 91.4, 91.4) is False
