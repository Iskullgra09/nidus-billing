"""phase B5 org fiscal profile and Hacienda credentials

Revision ID: a8b9c0d1e2f3
Revises: f6a7b8c9d0e1
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = (
    "organization_fiscal_profile",
    "organization_hacienda_credential",
)


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
        "organization_fiscal_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("trade_name", sa.String(length=255), nullable=True),
        sa.Column("identification_type", sa.String(length=32), nullable=False),
        sa.Column("identification_number", sa.String(length=32), nullable=False),
        sa.Column("economic_activity_code", sa.String(length=16), nullable=True),
        sa.Column("branch_code", sa.String(length=16), nullable=True),
        sa.Column("province", sa.String(length=64), nullable=True),
        sa.Column("canton", sa.String(length=64), nullable=True),
        sa.Column("district", sa.String(length=64), nullable=True),
        sa.Column("other_signs", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="CR"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "identification_type IN ('fisica', 'juridica', 'dimex', 'nite', 'extranjero')",
            name="ck_organization_fiscal_profile_id_type",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_organization_fiscal_profile_organization_id"),
    )
    op.create_index(
        op.f("ix_organization_fiscal_profile_organization_id"),
        "organization_fiscal_profile",
        ["organization_id"],
    )
    op.create_index(op.f("ix_organization_fiscal_profile_id"), "organization_fiscal_profile", ["id"])

    op.create_table(
        "organization_hacienda_credential",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("environment", sa.String(length=16), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("p12_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("p12_password_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("pin_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("oauth_client_id", sa.String(length=255), nullable=True),
        sa.Column("oauth_client_secret_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "environment IN ('sandbox', 'production')",
            name="ck_organization_hacienda_credential_environment",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_organization_hacienda_credential_organization_id"),
    )
    op.create_index(
        op.f("ix_organization_hacienda_credential_organization_id"),
        "organization_hacienda_credential",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_organization_hacienda_credential_id"),
        "organization_hacienda_credential",
        ["id"],
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.drop_table(table)
