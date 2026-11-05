"""phase B9 quotes + quote lines + RLS

Revision ID: a1b2c3d4e5f6
Revises: f4a5b6c7d8e9
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = ("quote", "quote_line")


def _enable_rls(table: str) -> None:
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {table} TO nidus_billing_app;")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"""
        CREATE POLICY {table}_isolation_policy ON {table} AS PERMISSIVE FOR ALL TO nidus_billing_app
        USING (
            organization_id::text = current_setting('app.current_organization_id', TRUE)
            OR current_setting('app.current_organization_id', TRUE) = ''
        )
        WITH CHECK (
            organization_id::text = current_setting('app.current_organization_id', TRUE)
            OR current_setting('app.current_organization_id', TRUE) = ''
        );
    """)


def upgrade() -> None:
    op.create_table(
        "quote",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CRC"),
        sa.Column("exchange_rate", sa.Numeric(18, 5), nullable=True),
        sa.Column("exchange_rate_date", sa.Date(), nullable=True),
        sa.Column("reference_number", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("converted_invoice_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'rejected', 'converted')",
            name="ck_quote_status",
        ),
        sa.CheckConstraint("currency IN ('CRC', 'USD')", name="ck_quote_currency"),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customer.id"]),
        sa.ForeignKeyConstraint(["converted_invoice_id"], ["invoice.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_id", "quote", ["id"], unique=False)
    op.create_index("ix_quote_organization_id", "quote", ["organization_id"], unique=False)
    op.create_index("ix_quote_deleted_at", "quote", ["deleted_at"], unique=False)
    op.create_index("ix_quote_customer_id", "quote", ["customer_id"], unique=False)
    op.create_index("ix_quote_converted_invoice_id", "quote", ["converted_invoice_id"], unique=False)
    op.create_index("ix_quote_org_status", "quote", ["organization_id", "status"], unique=False)
    op.create_index("ix_quote_org_customer", "quote", ["organization_id", "customer_id"], unique=False)

    op.create_table(
        "quote_line",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False, server_default="unit"),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=True),
        sa.Column("tax_code", sa.String(length=2), nullable=True),
        sa.Column("cabys_code", sa.String(length=16), nullable=True),
        sa.Column("line_subtotal", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("line_tax", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["quote_id"], ["quote.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_line_id", "quote_line", ["id"], unique=False)
    op.create_index("ix_quote_line_organization_id", "quote_line", ["organization_id"], unique=False)
    op.create_index("ix_quote_line_quote_id", "quote_line", ["quote_id"], unique=False)
    op.create_index(
        "ix_quote_line_quote_number",
        "quote_line",
        ["quote_id", "line_number"],
        unique=True,
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_quote_line_quote_number", table_name="quote_line")
    op.drop_index("ix_quote_line_quote_id", table_name="quote_line")
    op.drop_index("ix_quote_line_organization_id", table_name="quote_line")
    op.drop_index("ix_quote_line_id", table_name="quote_line")
    op.drop_table("quote_line")

    op.drop_index("ix_quote_org_customer", table_name="quote")
    op.drop_index("ix_quote_org_status", table_name="quote")
    op.drop_index("ix_quote_converted_invoice_id", table_name="quote")
    op.drop_index("ix_quote_customer_id", table_name="quote")
    op.drop_index("ix_quote_deleted_at", table_name="quote")
    op.drop_index("ix_quote_organization_id", table_name="quote")
    op.drop_index("ix_quote_id", table_name="quote")
    op.drop_table("quote")
