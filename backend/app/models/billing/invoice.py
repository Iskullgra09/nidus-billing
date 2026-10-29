from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import InvoiceStatus, PaymentCondition


class Invoice(UUIDMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, table=True):
    __tablename__ = "invoice"

    customer_id: UUID = Field(foreign_key="customer.id", nullable=False, index=True)
    payment_condition: str = Field(
        default=PaymentCondition.CONTADO.value,
        max_length=16,
        nullable=False,
        sa_column_kwargs={"server_default": PaymentCondition.CONTADO.value},
    )
    status: str = Field(
        default=InvoiceStatus.DRAFT.value,
        max_length=16,
        nullable=False,
        sa_column_kwargs={"server_default": InvoiceStatus.DRAFT.value},
    )
    currency: str = Field(default="CRC", max_length=3, nullable=False)
    document_number: Optional[str] = Field(default=None, max_length=64)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)
    issued_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    due_date: Optional[date] = Field(default=None)
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
    amount_paid: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    balance_due: Decimal = Field(
        default=Decimal("0"),
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False, server_default="0"),
    )

    __table_args__ = (
        sa.Index("ix_invoice_org_status", "organization_id", "status"),
        sa.Index("ix_invoice_org_customer", "organization_id", "customer_id"),
        sa.Index(
            "ix_invoice_org_document_number",
            "organization_id",
            "document_number",
            unique=True,
            postgresql_where=sa.text("document_number IS NOT NULL"),
        ),
        sa.CheckConstraint(
            "payment_condition IN ('contado', 'credito')",
            name="ck_invoice_payment_condition",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'issued', 'partial', 'paid', 'void')",
            name="ck_invoice_status",
        ),
        sa.CheckConstraint(
            "currency IN ('CRC', 'USD')",
            name="ck_invoice_currency",
        ),
    )


class InvoiceLine(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "invoice_line"

    invoice_id: UUID = Field(foreign_key="invoice.id", nullable=False, index=True)
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
        sa.Index("ix_invoice_line_invoice_number", "invoice_id", "line_number", unique=True),
    )
