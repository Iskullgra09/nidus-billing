from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin


class Supplier(UUIDMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, table=True):
    name: str = Field(max_length=255, nullable=False)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    identification_type: Optional[str] = Field(default=None, max_length=32)
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        sa.Index("ix_supplier_org_name", "organization_id", "name"),
        sa.Index(
            "ix_supplier_org_tax_id_active",
            "organization_id",
            "tax_id",
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL AND tax_id IS NOT NULL"),
        ),
        sa.CheckConstraint(
            "identification_type IS NULL OR identification_type IN "
            "('fisica', 'juridica', 'dimex', 'nite', 'extranjero')",
            name="ck_supplier_identification_type",
        ),
    )
