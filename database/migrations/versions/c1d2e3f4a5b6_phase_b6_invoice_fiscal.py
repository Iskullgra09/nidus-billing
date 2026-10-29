"""phase B6 invoice_fiscal and currency/tax codes for Hacienda XML 4.4

Revision ID: c1d2e3f4a5b6
Revises: a8b9c0d1e2f3
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
    op.execute(
        "UPDATE invoice SET currency = 'CRC' "
        "WHERE currency IS NULL OR currency NOT IN ('CRC', 'USD')"
    )
    op.create_check_constraint(
        "ck_invoice_currency",
        "invoice",
        "currency IN ('CRC', 'USD')",
    )

    op.add_column("invoice_line", sa.Column("tax_code", sa.String(length=2), nullable=True))
    op.add_column("invoice_line", sa.Column("cabys_code", sa.String(length=16), nullable=True))

    op.add_column(
        "customer",
        sa.Column("identification_type", sa.String(length=32), nullable=True),
    )
    op.create_check_constraint(
        "ck_customer_identification_type",
        "customer",
        "identification_type IS NULL OR identification_type IN "
        "('fisica', 'juridica', 'dimex', 'nite', 'extranjero')",
    )
    op.add_column(
        "supplier",
        sa.Column("identification_type", sa.String(length=32), nullable=True),
    )
    op.create_check_constraint(
        "ck_supplier_identification_type",
        "supplier",
        "identification_type IS NULL OR identification_type IN "
        "('fisica', 'juridica', 'dimex', 'nite', 'extranjero')",
    )

    op.drop_constraint("ck_document_series_doc_type", "document_series", type_="check")
    op.create_check_constraint(
        "ck_document_series_doc_type",
        "document_series",
        "doc_type IN ('invoice', 'fe')",
    )

    op.create_table(
        "invoice_fiscal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("clave", sa.String(length=50), nullable=True),
        sa.Column("consecutive", sa.String(length=20), nullable=True),
        sa.Column("supply_situation", sa.String(length=1), nullable=False),
        sa.Column("security_code", sa.String(length=8), nullable=True),
        sa.Column("xml_unsigned", sa.Text(), nullable=True),
        sa.Column("xml_signed", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mh_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mh_status_raw", sa.String(length=64), nullable=True),
        sa.Column("mh_message", sa.String(length=2000), nullable=True),
        sa.Column("mh_response_xml", sa.Text(), nullable=True),
        sa.Column("mock_mode", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "document_type IN ('01', '02', '03', '04')",
            name="ck_invoice_fiscal_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'processing', 'accepted', 'rejected', 'error')",
            name="ck_invoice_fiscal_status",
        ),
        sa.CheckConstraint(
            "supply_situation IN ('1', '2', '3')",
            name="ck_invoice_fiscal_supply_situation",
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", name="uq_invoice_fiscal_invoice_id"),
        sa.UniqueConstraint("organization_id", "clave", name="uq_invoice_fiscal_org_clave"),
    )
    op.create_index(
        op.f("ix_invoice_fiscal_organization_id"),
        "invoice_fiscal",
        ["organization_id"],
    )
    op.create_index(op.f("ix_invoice_fiscal_invoice_id"), "invoice_fiscal", ["invoice_id"])
    op.create_index(op.f("ix_invoice_fiscal_clave"), "invoice_fiscal", ["clave"])
    op.create_index(op.f("ix_invoice_fiscal_id"), "invoice_fiscal", ["id"])

    _enable_rls("invoice_fiscal")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS invoice_fiscal_isolation_policy ON invoice_fiscal;")
    op.execute("ALTER TABLE invoice_fiscal DISABLE ROW LEVEL SECURITY;")
    op.drop_table("invoice_fiscal")

    op.drop_constraint("ck_document_series_doc_type", "document_series", type_="check")
    op.create_check_constraint(
        "ck_document_series_doc_type",
        "document_series",
        "doc_type IN ('invoice')",
    )

    op.drop_constraint("ck_supplier_identification_type", "supplier", type_="check")
    op.drop_column("supplier", "identification_type")
    op.drop_constraint("ck_customer_identification_type", "customer", type_="check")
    op.drop_column("customer", "identification_type")

    op.drop_column("invoice_line", "cabys_code")
    op.drop_column("invoice_line", "tax_code")

    op.drop_constraint("ck_invoice_currency", "invoice", type_="check")
