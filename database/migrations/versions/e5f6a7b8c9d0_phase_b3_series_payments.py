"""phase B3 document series, payments, invoice balances

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = ("document_series", "invoice_payment")


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
        "document_series",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False, server_default="invoice"),
        sa.Column("prefix", sa.String(length=32), nullable=False, server_default="INV-"),
        sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("padding", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("doc_type IN ('invoice')", name="ck_document_series_doc_type"),
        sa.CheckConstraint("next_number >= 1", name="ck_document_series_next_number"),
        sa.CheckConstraint("padding >= 1 AND padding <= 12", name="ck_document_series_padding"),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_series_id", "document_series", ["id"], unique=False)
    op.create_index("ix_document_series_organization_id", "document_series", ["organization_id"], unique=False)
    op.create_index(
        "ix_document_series_org_type",
        "document_series",
        ["organization_id", "doc_type"],
        unique=True,
    )

    op.add_column("invoice", sa.Column("document_number", sa.String(length=64), nullable=True))
    op.add_column(
        "invoice",
        sa.Column("amount_paid", sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    op.add_column(
        "invoice",
        sa.Column("balance_due", sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    op.execute("ALTER TABLE invoice DROP CONSTRAINT IF EXISTS ck_invoice_status;")
    op.create_check_constraint(
        "ck_invoice_status",
        "invoice",
        "status IN ('draft', 'issued', 'partial', 'paid', 'void')",
    )
    op.create_index(
        "ix_invoice_org_document_number",
        "invoice",
        ["organization_id", "document_number"],
        unique=True,
        postgresql_where=sa.text("document_number IS NOT NULL"),
    )

    op.create_table(
        "invoice_payment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False, server_default="cash"),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("method IN ('cash', 'transfer', 'card', 'other')", name="ck_invoice_payment_method"),
        sa.CheckConstraint("amount > 0", name="ck_invoice_payment_amount"),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_payment_id", "invoice_payment", ["id"], unique=False)
    op.create_index("ix_invoice_payment_organization_id", "invoice_payment", ["organization_id"], unique=False)
    op.create_index("ix_invoice_payment_invoice_id", "invoice_payment", ["invoice_id"], unique=False)
    op.create_index(
        "ix_invoice_payment_org_invoice",
        "invoice_payment",
        ["organization_id", "invoice_id"],
        unique=False,
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_invoice_payment_org_invoice", table_name="invoice_payment")
    op.drop_index("ix_invoice_payment_invoice_id", table_name="invoice_payment")
    op.drop_index("ix_invoice_payment_organization_id", table_name="invoice_payment")
    op.drop_index("ix_invoice_payment_id", table_name="invoice_payment")
    op.drop_table("invoice_payment")

    op.drop_index("ix_invoice_org_document_number", table_name="invoice")
    op.execute("ALTER TABLE invoice DROP CONSTRAINT IF EXISTS ck_invoice_status;")
    op.create_check_constraint(
        "ck_invoice_status",
        "invoice",
        "status IN ('draft', 'issued', 'void')",
    )
    op.drop_column("invoice", "balance_due")
    op.drop_column("invoice", "amount_paid")
    op.drop_column("invoice", "document_number")

    op.drop_index("ix_document_series_org_type", table_name="document_series")
    op.drop_index("ix_document_series_organization_id", table_name="document_series")
    op.drop_index("ix_document_series_id", table_name="document_series")
    op.drop_table("document_series")
