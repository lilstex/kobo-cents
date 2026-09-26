from decimal import Decimal


def floatify(row: dict) -> dict:
    """Postgres Numeric columns come back as decimal.Decimal, per
    asyncpg/SQLAlchemy, and Python refuses to mix float and Decimal in
    arithmetic. Every DB-sourced row bound for a plain-float function
    (app/services/scoring.py's compute_raw_metrics, the sanity-check
    comparisons) gets normalized here, once, at the boundary, shared
    by the refresh job and the read-path API rather than each caller
    needing to know to convert."""
    return {
        key: float(value) if isinstance(value, Decimal) else value for key, value in row.items()
    }
