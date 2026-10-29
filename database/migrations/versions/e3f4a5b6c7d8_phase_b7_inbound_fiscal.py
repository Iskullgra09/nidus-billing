"""phase B7 inbound fiscal documents bandeja

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
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
    op.create_table(
        "inbound_fiscal_document",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=True),
        sa.Column("clave", sa.String(length=50), nullable=False),
        sa.Column("consecutive", sa.String(length=20), nullable=True),
        sa.Column("document_type", sa.String(length=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ingest_channel", sa.String(length=32), nullable=False),
        sa.Column("emitter_identification_type", sa.String(length=2), nullable=True),
        sa.Column("emitter_identification_number", sa.String(length=32), nullable=True),
        sa.Column("emitter_name", sa.String(length=255), nullable=True),
        sa.Column("emitter_email", sa.String(length=255), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 5), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("tax_total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("xml_received", sa.Text(), nullable=False),
        sa.Column("mensaje_tipo", sa.String(length=1), nullable=True),
        sa.Column("mensaje_detalle", sa.String(length=2000), nullable=True),
        sa.Column("mensaje_xml_signed", sa.Text(), nullable=True),
        sa.Column("mensaje_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mh_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mh_status_raw", sa.String(length=64), nullable=True),
        sa.Column("mh_message", sa.String(length=2000), nullable=True),
        sa.Column("mh_response_xml", sa.Text(), nullable=True),
        sa.Column("mock_mode", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("received_at", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "document_type IN ('01', '02', '03', '04')",
            name="ck_inbound_fiscal_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'processing', 'accepted', 'rejected', 'error')",
            name="ck_inbound_fiscal_document_status",
        ),
        sa.CheckConstraint(
            "ingest_channel IN ('manual_upload', 'hacienda_sync', 'email')",
            name="ck_inbound_fiscal_document_ingest",
        ),
        sa.CheckConstraint(
            "currency IN ('CRC', 'USD')",
            name="ck_inbound_fiscal_document_currency",
        ),
        sa.CheckConstraint(
            "mensaje_tipo IS NULL OR mensaje_tipo IN ('1', '2', '3')",
            name="ck_inbound_fiscal_document_mensaje_tipo",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "clave",
            name="uq_inbound_fiscal_document_org_clave",
        ),
    )
    op.create_index(
        "ix_inbound_fiscal_document_clave",
        "inbound_fiscal_document",
        ["clave"],
    )
    op.create_index(
        "ix_inbound_fiscal_document_supplier_id",
        "inbound_fiscal_document",
        ["supplier_id"],
    )
    op.create_index(
        "ix_inbound_fiscal_document_org_status",
        "inbound_fiscal_document",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_inbound_fiscal_document_organization_id",
        "inbound_fiscal_document",
        ["organization_id"],
    )
    _enable_rls("inbound_fiscal_document")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS inbound_fiscal_document_isolation_policy ON inbound_fiscal_document;")
    op.execute("ALTER TABLE inbound_fiscal_document DISABLE ROW LEVEL SECURITY;")
    op.drop_table("inbound_fiscal_document")
