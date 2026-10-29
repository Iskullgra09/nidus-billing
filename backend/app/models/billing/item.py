from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin


class Item(UUIDMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, table=True):
    sku: Optional[str] = Field(default=None, max_length=64)
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None, max_length=2000)
    unit: str = Field(default="unit", max_length=32, nullable=False)
    unit_price: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    tax_rate: Optional[Decimal] = Field(
        default=None,
        sa_column=sa.Column(sa.Numeric(7, 4), nullable=True),
        description="Tax rate hint as percent (e.g. 13.0000)",
    )
    cabys_code: Optional[str] = Field(default=None, max_length=16)
    is_service: bool = Field(default=False, nullable=False)
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        sa.Index("ix_item_org_name", "organization_id", "name"),
        sa.Index(
            "ix_item_org_sku_active",
            "organization_id",
            "sku",
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL AND sku IS NOT NULL"),
        ),
    )
