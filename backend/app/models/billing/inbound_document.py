from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import (
    HaciendaDocumentType,
    HaciendaFiscalStatus,
    InboundIngestChannel,
)


class InboundFiscalDocument(UUIDMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, table=True):
    __tablename__ = "inbound_fiscal_document"

    supplier_id: Optional[UUID] = Field(default=None, foreign_key="supplier.id", index=True)
    clave: str = Field(max_length=50, nullable=False, index=True)
    consecutive: Optional[str] = Field(default=None, max_length=20)
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
    ingest_channel: str = Field(
        default=InboundIngestChannel.MANUAL_UPLOAD.value,
        max_length=32,
        nullable=False,
    )
    emitter_identification_type: Optional[str] = Field(default=None, max_length=2)
    emitter_identification_number: Optional[str] = Field(default=None, max_length=32)
    emitter_name: Optional[str] = Field(default=None, max_length=255)
    emitter_email: Optional[str] = Field(default=None, max_length=255)
    issued_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    currency: str = Field(default="CRC", max_length=3, nullable=False)
    exchange_rate: Optional[Decimal] = Field(
        default=None,
        sa_column=sa.Column(sa.Numeric(18, 5), nullable=True),
    )
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
    xml_received: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
    mensaje_tipo: Optional[str] = Field(default=None, max_length=1)
    mensaje_detalle: Optional[str] = Field(default=None, max_length=2000)
    mensaje_xml_signed: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    mensaje_submitted_at: Optional[datetime] = Field(
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
    notes: Optional[str] = Field(default=None, max_length=2000)
    received_at: date = Field(
        default_factory=date.today,
        sa_column=sa.Column(sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "organization_id",
            "clave",
            name="uq_inbound_fiscal_document_org_clave",
        ),
        sa.CheckConstraint(
            "document_type IN ('01', '02', '03', '04')",
            name="ck_inbound_fiscal_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'processing', 'accepted', 'rejected', 'error')",
            name="ck_inbound_fiscal_document_status",
        ),
        sa.CheckConstraint(
            "ingest_channel IN ('manual_upload', 'hacienda_sync', 'email')",
            name="ck_inbound_fiscal_document_ingest",
        ),
        sa.CheckConstraint(
            "currency IN ('CRC', 'USD')",
            name="ck_inbound_fiscal_document_currency",
        ),
        sa.CheckConstraint(
            "mensaje_tipo IS NULL OR mensaje_tipo IN ('1', '2', '3')",
            name="ck_inbound_fiscal_document_mensaje_tipo",
        ),
        sa.Index("ix_inbound_fiscal_document_org_status", "organization_id", "status"),
    )
