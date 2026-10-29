from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.billing.enums import (
    HaciendaEnvironment,
    IdentificationType,
    InvoiceCurrency,
    PaymentCondition,
    PaymentMethod,
)


class PartyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    identification_type: Optional[IdentificationType] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: bool = True


class PartyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    identification_type: Optional[IdentificationType] = None
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
    tax_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    cabys_code: Optional[str] = Field(default=None, max_length=16)


class InvoiceCreate(BaseModel):
    customer_id: UUID
    payment_condition: PaymentCondition = PaymentCondition.CONTADO
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    currency: InvoiceCurrency = InvoiceCurrency.CRC
    lines: list[InvoiceLineInput] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    payment_condition: Optional[PaymentCondition] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=64)
    currency: Optional[InvoiceCurrency] = None
    lines: Optional[list[InvoiceLineInput]] = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")


class InvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_at: Optional[datetime] = None
    method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = Field(default=None, max_length=2000)


class InvoiceSendEmail(BaseModel):
    to_email: Optional[EmailStr] = None
    subject: Optional[str] = Field(default=None, max_length=255)
    message: Optional[str] = Field(default=None, max_length=2000)


class FiscalProfileUpsert(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    trade_name: Optional[str] = Field(default=None, max_length=255)
    identification_type: IdentificationType = IdentificationType.JURIDICA
    identification_number: str = Field(min_length=1, max_length=32)
    economic_activity_code: Optional[str] = Field(default=None, max_length=16)
    branch_code: Optional[str] = Field(default=None, max_length=16)
    province: Optional[str] = Field(default=None, max_length=64)
    canton: Optional[str] = Field(default=None, max_length=64)
    district: Optional[str] = Field(default=None, max_length=64)
    other_signs: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[EmailStr] = None
    country_code: str = Field(default="CR", min_length=2, max_length=2)


class HaciendaCredentialUpsert(BaseModel):
    environment: HaciendaEnvironment = HaciendaEnvironment.SANDBOX
    username: Optional[str] = Field(default=None, max_length=255)
    p12_password: Optional[str] = Field(default=None, max_length=255)
    pin: Optional[str] = Field(default=None, max_length=64)
    oauth_client_id: Optional[str] = Field(default=None, max_length=255)
    oauth_client_secret: Optional[str] = Field(default=None, max_length=512)
