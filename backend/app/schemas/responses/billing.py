from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PartyResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemResponse(BaseModel):
    id: UUID
    organization_id: UUID
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    unit: str
    unit_price: Decimal
    tax_rate: Optional[Decimal] = None
    is_service: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
