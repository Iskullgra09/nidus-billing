from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import PaymentMethod


class InvoicePayment(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "invoice_payment"

    invoice_id: UUID = Field(foreign_key="invoice.id", nullable=False, index=True)
    amount: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(18, 4), nullable=False),
    )
    paid_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    method: str = Field(
        default=PaymentMethod.CASH.value,
        max_length=16,
        nullable=False,
    )
    notes: Optional[str] = Field(default=None, max_length=2000)

    __table_args__ = (
        sa.Index("ix_invoice_payment_org_invoice", "organization_id", "invoice_id"),
        sa.CheckConstraint(
            "method IN ('cash', 'transfer', 'card', 'other')",
            name="ck_invoice_payment_method",
        ),
        sa.CheckConstraint("amount > 0", name="ck_invoice_payment_amount"),
    )
