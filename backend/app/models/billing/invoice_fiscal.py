from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import HaciendaDocumentType, HaciendaFiscalStatus


class InvoiceFiscal(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "invoice_fiscal"

    invoice_id: UUID = Field(foreign_key="invoice.id", nullable=False, index=True)
    document_type: str = Field(
        default=HaciendaDocumentType.FE.value,
        max_length=2,
        nullable=False,
    )
    status: str = Field(
        default=HaciendaFiscalStatus.PENDING.value,
        max_length=32,
        nullable=False,
    )
    clave: Optional[str] = Field(default=None, max_length=50, index=True)
    consecutive: Optional[str] = Field(default=None, max_length=20)
    supply_situation: str = Field(default="1", max_length=1, nullable=False)
    security_code: Optional[str] = Field(default=None, max_length=8)
    xml_unsigned: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    xml_signed: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text(), nullable=True))
    signed_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    submitted_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    mh_response_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    mh_status_raw: Optional[str] = Field(default=None, max_length=64)
    mh_message: Optional[str] = Field(default=None, max_length=2000)
    mh_response_xml: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    mock_mode: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={"server_default": sa.text("true")},
    )

    __table_args__ = (
        sa.UniqueConstraint("invoice_id", name="uq_invoice_fiscal_invoice_id"),
        sa.UniqueConstraint(
            "organization_id",
            "clave",
            name="uq_invoice_fiscal_org_clave",
        ),
        sa.CheckConstraint(
            "document_type IN ('01', '02', '03', '04')",
            name="ck_invoice_fiscal_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'processing', 'accepted', 'rejected', 'error')",
            name="ck_invoice_fiscal_status",
        ),
        sa.CheckConstraint(
            "supply_situation IN ('1', '2', '3')",
            name="ck_invoice_fiscal_supply_situation",
        ),
    )
