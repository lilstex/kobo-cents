# Reuses the same meaningful-delta idea docs/backend-architecture/
# 01.md designed for alert matching, applied here first as a trust
# gate, per 00.md: a figure that moved past a threshold with no real
# event behind it gets flagged for review rather than silently
# overwriting a previously good value. The exact thresholds below are
# a reasonable starting point, not validated against real NG data yet,
# same honest status as the rate-limit numbers from Phase 2, worth
# tuning once there's real data to tune them against.

FUNDAMENTAL_CHANGE_THRESHOLD = 0.5  # 50% cycle-over-cycle move
PRICE_CHANGE_THRESHOLD = 0.3  # 30% single-cycle move


def is_suspicious_change(previous: float | None, new: float | None, threshold: float) -> bool:
    """True if `new` moved past `threshold` relative to `previous`.
    A previously-missing value becoming present, or a value going
    missing, is never itself suspicious, that's normal for a company
    that starts or stops reporting a figure."""
    if previous is None or new is None:
        return False
    if previous == 0:
        return new != 0
    relative_change = abs(new - previous) / abs(previous)
    return relative_change > threshold
