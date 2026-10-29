import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import DocumentSeriesType


class DocumentSeries(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "document_series"

    doc_type: str = Field(
        default=DocumentSeriesType.INVOICE.value,
        max_length=32,
        nullable=False,
    )
    prefix: str = Field(default="INV-", max_length=32, nullable=False)
    next_number: int = Field(default=1, nullable=False)
    padding: int = Field(default=6, nullable=False)

    __table_args__ = (
        sa.Index(
            "ix_document_series_org_type",
            "organization_id",
            "doc_type",
            unique=True,
        ),
        sa.CheckConstraint(
            "doc_type IN ('invoice', 'fe')",
            name="ck_document_series_doc_type",
        ),
        sa.CheckConstraint("next_number >= 1", name="ck_document_series_next_number"),
        sa.CheckConstraint("padding >= 1 AND padding <= 12", name="ck_document_series_padding"),
    )
