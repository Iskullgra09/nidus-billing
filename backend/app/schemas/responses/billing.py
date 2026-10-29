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
    identification_type: Optional[str] = None
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
    tax_code: Optional[str] = None
    cabys_code: Optional[str] = None
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
    hacienda_status: Optional[str] = None
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


class FiscalProfileResponse(BaseModel):
    id: UUID
    organization_id: UUID
    legal_name: str
    trade_name: Optional[str] = None
    identification_type: str
    identification_number: str
    economic_activity_code: Optional[str] = None
    branch_code: Optional[str] = None
    province: Optional[str] = None
    canton: Optional[str] = None
    district: Optional[str] = None
    other_signs: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    country_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HaciendaCredentialStatusResponse(BaseModel):
    configured: bool
    environment: str
    username: Optional[str] = None
    has_p12: bool
    has_p12_password: bool
    has_pin: bool
    has_oauth_client_secret: bool
    oauth_client_id: Optional[str] = None
    updated_at: Optional[datetime] = None


class InvoiceFiscalResponse(BaseModel):
    id: UUID
    organization_id: UUID
    invoice_id: UUID
    document_type: str
    status: str
    clave: Optional[str] = None
    consecutive: Optional[str] = None
    supply_situation: str
    signed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    mh_response_at: Optional[datetime] = None
    mh_status_raw: Optional[str] = None
    mh_message: Optional[str] = None
    mock_mode: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

