"""phase B4 invoice outbound email delivery log

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = ("invoice_email_delivery",)


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
        "invoice_email_delivery",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('sent', 'failed', 'mocked')",
            name="ck_invoice_email_delivery_status",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_invoice_email_delivery_org_invoice",
        "invoice_email_delivery",
        ["organization_id", "invoice_id"],
    )
    op.create_index(
        op.f("ix_invoice_email_delivery_invoice_id"),
        "invoice_email_delivery",
        ["invoice_id"],
    )
    op.create_index(
        op.f("ix_invoice_email_delivery_organization_id"),
        "invoice_email_delivery",
        ["organization_id"],
    )
    op.create_index(op.f("ix_invoice_email_delivery_id"), "invoice_email_delivery", ["id"])

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in _RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index(op.f("ix_invoice_email_delivery_id"), table_name="invoice_email_delivery")
    op.drop_index(op.f("ix_invoice_email_delivery_organization_id"), table_name="invoice_email_delivery")
    op.drop_index(op.f("ix_invoice_email_delivery_invoice_id"), table_name="invoice_email_delivery")
    op.drop_index("ix_invoice_email_delivery_org_invoice", table_name="invoice_email_delivery")
    op.drop_table("invoice_email_delivery")
