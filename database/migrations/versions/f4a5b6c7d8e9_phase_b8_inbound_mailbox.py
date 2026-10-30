"""phase B8 per-org inbound purchase mailbox

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-10-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
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
        "organization_inbound_mailbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("local_part", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            name="uq_organization_inbound_mailbox_organization_id",
        ),
        sa.UniqueConstraint(
            "local_part",
            name="uq_organization_inbound_mailbox_local_part",
        ),
    )
    op.create_index(
        op.f("ix_organization_inbound_mailbox_organization_id"),
        "organization_inbound_mailbox",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_organization_inbound_mailbox_id"),
        "organization_inbound_mailbox",
        ["id"],
    )
    op.create_index(
        "ix_organization_inbound_mailbox_local_part",
        "organization_inbound_mailbox",
        ["local_part"],
    )
    _enable_rls("organization_inbound_mailbox")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS organization_inbound_mailbox_isolation_policy "
        "ON organization_inbound_mailbox;"
    )
    op.execute("ALTER TABLE organization_inbound_mailbox DISABLE ROW LEVEL SECURITY;")
    op.drop_table("organization_inbound_mailbox")
