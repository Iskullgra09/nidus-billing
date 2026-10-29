from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import HaciendaEnvironment


class OrganizationHaciendaCredential(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "organization_hacienda_credential"

    environment: str = Field(
        default=HaciendaEnvironment.SANDBOX.value,
        max_length=16,
        nullable=False,
    )
    username: Optional[str] = Field(default=None, max_length=255)
    p12_ciphertext: Optional[bytes] = Field(
        default=None,
        sa_column=sa.Column(sa.LargeBinary(), nullable=True),
    )
    p12_password_ciphertext: Optional[bytes] = Field(
        default=None,
        sa_column=sa.Column(sa.LargeBinary(), nullable=True),
    )
    pin_ciphertext: Optional[bytes] = Field(
        default=None,
        sa_column=sa.Column(sa.LargeBinary(), nullable=True),
    )
    oauth_client_id: Optional[str] = Field(default=None, max_length=255)
    oauth_client_secret_ciphertext: Optional[bytes] = Field(
        default=None,
        sa_column=sa.Column(sa.LargeBinary(), nullable=True),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "organization_id",
            name="uq_organization_hacienda_credential_organization_id",
        ),
        sa.CheckConstraint(
            "environment IN ('sandbox', 'production')",
            name="ck_organization_hacienda_credential_environment",
        ),
    )
