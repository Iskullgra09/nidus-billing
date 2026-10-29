from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PartyFilter(BaseModel):
    q: Optional[str] = Field(default=None, description="Search name, email, or tax_id")
    is_active: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class ItemFilter(BaseModel):
    q: Optional[str] = Field(default=None, description="Search name or SKU")
    is_active: Optional[bool] = None
    is_service: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class InvoiceFilter(BaseModel):
    q: Optional[str] = Field(default=None, description="Search reference or customer name")
    status: Optional[str] = None
    payment_condition: Optional[str] = None
    customer_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
