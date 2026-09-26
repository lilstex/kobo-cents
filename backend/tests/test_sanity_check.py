from app.integrations.market_data.sanity_check import (
    FUNDAMENTAL_CHANGE_THRESHOLD,
    is_suspicious_change,
)


def test_a_small_change_is_not_suspicious():
    assert is_suspicious_change(100.0, 105.0, FUNDAMENTAL_CHANGE_THRESHOLD) is False


def test_a_large_change_is_suspicious():
    assert is_suspicious_change(100.0, 200.0, FUNDAMENTAL_CHANGE_THRESHOLD) is True


def test_a_newly_appearing_value_is_never_suspicious():
    assert is_suspicious_change(None, 1_000_000.0, FUNDAMENTAL_CHANGE_THRESHOLD) is False


def test_a_value_that_disappears_is_never_suspicious():
    assert is_suspicious_change(1_000_000.0, None, FUNDAMENTAL_CHANGE_THRESHOLD) is False


def test_zero_to_nonzero_is_suspicious():
    assert is_suspicious_change(0.0, 5.0, FUNDAMENTAL_CHANGE_THRESHOLD) is True


def test_zero_to_zero_is_not_suspicious():
    assert is_suspicious_change(0.0, 0.0, FUNDAMENTAL_CHANGE_THRESHOLD) is False
