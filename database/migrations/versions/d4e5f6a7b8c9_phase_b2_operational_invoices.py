"""phase B2 operational invoices + lines + RLS

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = ("invoice", "invoice_line")


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
        "invoice",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("payment_condition", sa.String(length=16), nullable=False, server_default="contado"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CRC"),
        sa.Column("reference_number", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("payment_condition IN ('contado', 'credito')", name="ck_invoice_payment_condition"),
        sa.CheckConstraint("status IN ('draft', 'issued', 'void')", name="ck_invoice_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_id", "invoice", ["id"], unique=False)
    op.create_index("ix_invoice_organization_id", "invoice", ["organization_id"], unique=False)
    op.create_index("ix_invoice_deleted_at", "invoice", ["deleted_at"], unique=False)
    op.create_index("ix_invoice_customer_id", "invoice", ["customer_id"], unique=False)
    op.create_index("ix_invoice_org_status", "invoice", ["organization_id", "status"], unique=False)
    op.create_index("ix_invoice_org_customer", "invoice", ["organization_id", "customer_id"], unique=False)

    op.create_table(
        "invoice_line",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False, server_default="unit"),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=True),
        sa.Column("line_subtotal", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("line_tax", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_line_id", "invoice_line", ["id"], unique=False)
    op.create_index("ix_invoice_line_organization_id", "invoice_line", ["organization_id"], unique=False)
    op.create_index("ix_invoice_line_invoice_id", "invoice_line", ["invoice_id"], unique=False)
    op.create_index(
        "ix_invoice_line_invoice_number",
        "invoice_line",
        ["invoice_id", "line_number"],
        unique=True,
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_invoice_line_invoice_number", table_name="invoice_line")
    op.drop_index("ix_invoice_line_invoice_id", table_name="invoice_line")
    op.drop_index("ix_invoice_line_organization_id", table_name="invoice_line")
    op.drop_index("ix_invoice_line_id", table_name="invoice_line")
    op.drop_table("invoice_line")

    op.drop_index("ix_invoice_org_customer", table_name="invoice")
    op.drop_index("ix_invoice_org_status", table_name="invoice")
    op.drop_index("ix_invoice_customer_id", table_name="invoice")
    op.drop_index("ix_invoice_deleted_at", table_name="invoice")
    op.drop_index("ix_invoice_organization_id", table_name="invoice")
    op.drop_index("ix_invoice_id", table_name="invoice")
    op.drop_table("invoice")
