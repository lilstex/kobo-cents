"""enable pg_trgm and add trigram search indexes

Revision ID: b24c66fcebaf
Revises: 711eb02dd360
Create Date: 2026-09-25 18:13:39.070719

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b24c66fcebaf"
down_revision: str | Sequence[str] | None = "711eb02dd360"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # gin_trgm_ops isn't built in, the two GIN indexes below fail to
    # create without this extension enabled first.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_stocks_company_name_trgm",
        "stocks",
        ["company_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"company_name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_stocks_ticker_trgm",
        "stocks",
        ["ticker"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"ticker": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_stocks_ticker_trgm",
        table_name="stocks",
        postgresql_using="gin",
        postgresql_ops={"ticker": "gin_trgm_ops"},
    )
    op.drop_index(
        "ix_stocks_company_name_trgm",
        table_name="stocks",
        postgresql_using="gin",
        postgresql_ops={"company_name": "gin_trgm_ops"},
    )
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
