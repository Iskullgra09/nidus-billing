from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import InvoiceEmailStatus


class InvoiceEmailDelivery(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "invoice_email_delivery"

    invoice_id: UUID = Field(foreign_key="invoice.id", nullable=False, index=True)
    to_email: str = Field(max_length=255, nullable=False)
    subject: str = Field(max_length=255, nullable=False)
    status: str = Field(
        default=InvoiceEmailStatus.SENT.value,
        max_length=16,
        nullable=False,
    )
    error_message: Optional[str] = Field(default=None, max_length=2000)
    sent_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    actor_user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")

    __table_args__ = (
        sa.Index("ix_invoice_email_delivery_org_invoice", "organization_id", "invoice_id"),
        sa.CheckConstraint(
            "status IN ('sent', 'failed', 'mocked')",
            name="ck_invoice_email_delivery_status",
        ),
    )
