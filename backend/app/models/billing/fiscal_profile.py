from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field

from app.models.base import TenantMixin, TimestampMixin, UUIDMixin
from app.models.billing.enums import IdentificationType


class OrganizationFiscalProfile(UUIDMixin, TimestampMixin, TenantMixin, table=True):
    __tablename__ = "organization_fiscal_profile"

    legal_name: str = Field(max_length=255, nullable=False)
    trade_name: Optional[str] = Field(default=None, max_length=255)
    identification_type: str = Field(
        default=IdentificationType.JURIDICA.value,
        max_length=32,
        nullable=False,
    )
    identification_number: str = Field(max_length=32, nullable=False)
    economic_activity_code: Optional[str] = Field(default=None, max_length=16)
    branch_code: Optional[str] = Field(default=None, max_length=16)
    province: Optional[str] = Field(default=None, max_length=64)
    canton: Optional[str] = Field(default=None, max_length=64)
    district: Optional[str] = Field(default=None, max_length=64)
    other_signs: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[str] = Field(default=None, max_length=255)
    country_code: str = Field(default="CR", max_length=2, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint(
            "organization_id",
            name="uq_organization_fiscal_profile_organization_id",
        ),
        sa.CheckConstraint(
            "identification_type IN ('fisica', 'juridica', 'dimex', 'nite', 'extranjero')",
            name="ck_organization_fiscal_profile_id_type",
        ),
    )
