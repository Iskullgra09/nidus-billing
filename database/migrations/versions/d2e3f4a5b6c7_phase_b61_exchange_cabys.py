"""phase B6.1 exchange rate on invoice and item cabys default

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invoice",
        sa.Column("exchange_rate", sa.Numeric(18, 5), nullable=True),
    )
    op.add_column(
        "invoice",
        sa.Column("exchange_rate_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "item",
        sa.Column("cabys_code", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("item", "cabys_code")
    op.drop_column("invoice", "exchange_rate_date")
    op.drop_column("invoice", "exchange_rate")
