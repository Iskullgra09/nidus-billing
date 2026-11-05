from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import QuoteStatus


class Quote(UUIDMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, table=True):
    __tablename__ = "quote"

    customer_id: UUID = Field(foreign_key="customer.id", nullable=False, index=True)
    status: str = Field(
        default=QuoteStatus.DRAFT.value,
        max_length=16,
        nullable=False,
        sa_column_kwargs={"server_default": QuoteStatus.DRAFT.value},
    )
    currency: str = Field(default="CRC", max_length=3, nullable=False)
    exchange_rate: Optional[Decimal] = Field(
        default=None,
        sa_column=sa.Column(sa.Numeric(18, 5), nullable=True),
    )
    exchange_rate_date: Optional[date] = Field(default=None)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)
    valid_until: Optional[date] = Field(default=None)
    subtotal: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    tax_total: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    total: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    converted_invoice_id: Optional[UUID] = Field(
        default=None,
        foreign_key="invoice.id",
        nullable=True,
        index=True,
    )

    __table_args__ = (
        sa.Index("ix_quote_org_status", "organization_id", "status"),
        sa.Index("ix_quote_org_customer", "organization_id", "customer_id"),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'rejected', 'converted')",
            name="ck_quote_status",
        ),
        sa.CheckConstraint(
            "currency IN ('CRC', 'USD')",
            name="ck_quote_currency",
        ),
    )


class QuoteLine(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "quote_line"

    quote_id: UUID = Field(foreign_key="quote.id", nullable=False, index=True)
    line_number: int = Field(nullable=False)
    item_id: Optional[UUID] = Field(default=None, foreign_key="item.id")
    description: str = Field(max_length=255, nullable=False)
    sku: Optional[str] = Field(default=None, max_length=64)
    unit: str = Field(default="unit", max_length=32, nullable=False)
    quantity: Decimal = Field(
        default=Decimal("1"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="1"),
    )
    unit_price: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    tax_rate: Optional[Decimal] = Field(
        default=None,
        sa_column=sa.Column(sa.Numeric(7, 4), nullable=True),
    )
    tax_code: Optional[str] = Field(default=None, max_length=2)
    cabys_code: Optional[str] = Field(default=None, max_length=16)
    line_subtotal: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    line_tax: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    line_total: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )

    __table_args__ = (
        sa.Index("ix_quote_line_quote_number", "quote_id", "line_number", unique=True),
    )
