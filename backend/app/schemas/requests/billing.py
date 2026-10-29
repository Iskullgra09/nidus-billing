from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PartyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: bool = True


class PartyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=2000)
    unit: str = Field(default="unit", min_length=1, max_length=32)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_service: bool = False
    is_active: bool = True


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    sku: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=2000)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=32)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_service: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")
