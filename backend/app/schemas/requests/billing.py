from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.billing.enums import PaymentCondition, PaymentMethod


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


class InvoiceLineInput(BaseModel):
    item_id: Optional[UUID] = None
    description: str = Field(min_length=1, max_length=255)
    sku: Optional[str] = Field(default=None, max_length=64)
    unit: str = Field(default="unit", min_length=1, max_length=32)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)


class InvoiceCreate(BaseModel):
    customer_id: UUID
    payment_condition: PaymentCondition = PaymentCondition.CONTADO
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    currency: str = Field(default="CRC", min_length=3, max_length=3)
    lines: list[InvoiceLineInput] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    payment_condition: Optional[PaymentCondition] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    lines: Optional[list[InvoiceLineInput]] = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class InvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_at: Optional[datetime] = None
    method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = Field(default=None, max_length=2000)
