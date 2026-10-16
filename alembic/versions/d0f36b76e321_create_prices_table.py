"""create prices table

Revision ID: d0f36b76e321
Revises:
Create Date: 2026-10-16 20:33:56.274193

"""

import sqlalchemy as sa

from alembic import op

revision: str = "d0f36b76e321"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("timestamp", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prices_ticker_timestamp", "prices", ["ticker", "timestamp"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_prices_ticker_timestamp", table_name="prices")
    op.drop_table("prices")
