"""Importing this package registers every table against
app.db.base.metadata. Alembic's env.py imports this module so
autogenerate sees the full schema, not whichever tables happened to
be imported first."""

from app.models import market_data, payments, portfolio, users

__all__ = ["market_data", "payments", "portfolio", "users"]
