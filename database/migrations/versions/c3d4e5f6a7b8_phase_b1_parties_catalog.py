"""phase B1 parties catalog: customer, supplier, item + RLS

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-10-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = ("customer", "supplier", "item")


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
        "customer",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("tax_id", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_id", "customer", ["id"], unique=False)
    op.create_index("ix_customer_organization_id", "customer", ["organization_id"], unique=False)
    op.create_index("ix_customer_deleted_at", "customer", ["deleted_at"], unique=False)
    op.create_index("ix_customer_org_name", "customer", ["organization_id", "name"], unique=False)
    op.create_index(
        "ix_customer_org_tax_id_active",
        "customer",
        ["organization_id", "tax_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND tax_id IS NOT NULL"),
    )

    op.create_table(
        "supplier",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("tax_id", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supplier_id", "supplier", ["id"], unique=False)
    op.create_index("ix_supplier_organization_id", "supplier", ["organization_id"], unique=False)
    op.create_index("ix_supplier_deleted_at", "supplier", ["deleted_at"], unique=False)
    op.create_index("ix_supplier_org_name", "supplier", ["organization_id", "name"], unique=False)
    op.create_index(
        "ix_supplier_org_tax_id_active",
        "supplier",
        ["organization_id", "tax_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND tax_id IS NOT NULL"),
    )

    op.create_table(
        "item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False, server_default="unit"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=True),
        sa.Column("is_service", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_id", "item", ["id"], unique=False)
    op.create_index("ix_item_organization_id", "item", ["organization_id"], unique=False)
    op.create_index("ix_item_deleted_at", "item", ["deleted_at"], unique=False)
    op.create_index("ix_item_org_name", "item", ["organization_id", "name"], unique=False)
    op.create_index(
        "ix_item_org_sku_active",
        "item",
        ["organization_id", "sku"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND sku IS NOT NULL"),
    )

    for table in _RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_item_org_sku_active", table_name="item")
    op.drop_index("ix_item_org_name", table_name="item")
    op.drop_index("ix_item_deleted_at", table_name="item")
    op.drop_index("ix_item_organization_id", table_name="item")
    op.drop_index("ix_item_id", table_name="item")
    op.drop_table("item")

    op.drop_index("ix_supplier_org_tax_id_active", table_name="supplier")
    op.drop_index("ix_supplier_org_name", table_name="supplier")
    op.drop_index("ix_supplier_deleted_at", table_name="supplier")
    op.drop_index("ix_supplier_organization_id", table_name="supplier")
    op.drop_index("ix_supplier_id", table_name="supplier")
    op.drop_table("supplier")

    op.drop_index("ix_customer_org_tax_id_active", table_name="customer")
    op.drop_index("ix_customer_org_name", table_name="customer")
    op.drop_index("ix_customer_deleted_at", table_name="customer")
    op.drop_index("ix_customer_organization_id", table_name="customer")
    op.drop_index("ix_customer_id", table_name="customer")
    op.drop_table("customer")
