import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin


class OrganizationInboundMailbox(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    """Per-org address for supplier FE emails → Facturas de compra."""

    __tablename__ = "organization_inbound_mailbox"

    local_part: str = Field(max_length=64, nullable=False, index=True)
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={"server_default": sa.text("true")},
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "organization_id",
            name="uq_organization_inbound_mailbox_organization_id",
        ),
        sa.UniqueConstraint(
            "local_part",
            name="uq_organization_inbound_mailbox_local_part",
        ),
    )
