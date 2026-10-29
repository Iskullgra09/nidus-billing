from datetime import date, datetime
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


class InvoiceLineResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    line_number: int
    item_id: Optional[UUID] = None
    description: str
    sku: Optional[str] = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Optional[Decimal] = None
    line_subtotal: Decimal
    line_tax: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoicePaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    paid_at: datetime
    method: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    payment_condition: str
    status: str
    currency: str
    document_number: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_date: Optional[date] = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    is_overdue: bool = False
    lines: list[InvoiceLineResponse] = []
    payments: list[InvoicePaymentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    payment_condition: str
    status: str
    currency: str
    document_number: Optional[str] = None
    reference_number: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_date: Optional[date] = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceEmailDeliveryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    invoice_id: UUID
    to_email: str
    subject: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    actor_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
