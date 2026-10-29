from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ScopeGuard, get_current_tenant_session, get_jwt_payload, get_language
from app.core.exceptions.base import AuthenticationError
from app.core.i18n.service import i18n
from app.models.identity.scopes import NidusScope
from app.schemas.filters.billing import InvoiceFilter, ItemFilter, PartyFilter
from app.schemas.requests.billing import (
    InvoiceCreate,
    InvoicePaymentCreate,
    InvoiceUpdate,
    ItemCreate,
    ItemUpdate,
    PartyCreate,
    PartyUpdate,
)
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.base import GenericResponse
from app.schemas.responses.billing import (
    InvoiceListItem,
    InvoicePaymentResponse,
    InvoiceResponse,
    ItemResponse,
    PartyResponse,
)
from app.schemas.responses.pagination import CursorPage
from app.services.billing import (
    CustomerService,
    InvoiceService,
    ItemService,
    PaymentService,
    SupplierService,
)

router = APIRouter()


def _require_org_id(payload: dict[str, Any]) -> UUID:
    raw_org_id = payload.get("org_id")
    if not raw_org_id:
        raise AuthenticationError(message_key="common.forbidden")
    return UUID(str(raw_org_id))


@router.get(
    "/customers",
    response_model=GenericResponse[CursorPage[PartyResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.CUSTOMER_READ))],
)
async def list_customers(
    pagination: CursorParams = Depends(),
    filters: PartyFilter = Depends(),
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await CustomerService.list_customers(session, pagination, filters)
    return GenericResponse(data=data, message=i18n.t("success.customers_retrieved", lang=lang))


@router.post(
    "/customers",
    response_model=GenericResponse[PartyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.CUSTOMER_WRITE))],
)
async def create_customer(
    data: PartyCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    customer = await CustomerService.create_customer(session, org_id, data)
    return GenericResponse(data=customer, message=i18n.t("success.customer_created", lang=lang))


@router.get(
    "/customers/{customer_id}",
    response_model=GenericResponse[PartyResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.CUSTOMER_READ))],
)
async def get_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    customer = await CustomerService.get_customer(session, customer_id)
    return GenericResponse(data=customer, message=i18n.t("success.customer_retrieved", lang=lang))


@router.patch(
    "/customers/{customer_id}",
    response_model=GenericResponse[PartyResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.CUSTOMER_WRITE))],
)
async def update_customer(
    customer_id: UUID,
    data: PartyUpdate,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    customer = await CustomerService.update_customer(session, customer_id, data)
    return GenericResponse(data=customer, message=i18n.t("success.customer_updated", lang=lang))


@router.delete(
    "/customers/{customer_id}",
    response_model=GenericResponse[None],
    dependencies=[Depends(ScopeGuard(NidusScope.CUSTOMER_WRITE))],
)
async def delete_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    await CustomerService.delete_customer(session, customer_id)
    return GenericResponse(message=i18n.t("success.customer_deleted", lang=lang))


@router.get(
    "/suppliers",
    response_model=GenericResponse[CursorPage[PartyResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.SUPPLIER_READ))],
)
async def list_suppliers(
    pagination: CursorParams = Depends(),
    filters: PartyFilter = Depends(),
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await SupplierService.list_suppliers(session, pagination, filters)
    return GenericResponse(data=data, message=i18n.t("success.suppliers_retrieved", lang=lang))


@router.post(
    "/suppliers",
    response_model=GenericResponse[PartyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.SUPPLIER_WRITE))],
)
async def create_supplier(
    data: PartyCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    supplier = await SupplierService.create_supplier(session, org_id, data)
    return GenericResponse(data=supplier, message=i18n.t("success.supplier_created", lang=lang))


@router.get(
    "/suppliers/{supplier_id}",
    response_model=GenericResponse[PartyResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.SUPPLIER_READ))],
)
async def get_supplier(
    supplier_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    supplier = await SupplierService.get_supplier(session, supplier_id)
    return GenericResponse(data=supplier, message=i18n.t("success.supplier_retrieved", lang=lang))


@router.patch(
    "/suppliers/{supplier_id}",
    response_model=GenericResponse[PartyResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.SUPPLIER_WRITE))],
)
async def update_supplier(
    supplier_id: UUID,
    data: PartyUpdate,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    supplier = await SupplierService.update_supplier(session, supplier_id, data)
    return GenericResponse(data=supplier, message=i18n.t("success.supplier_updated", lang=lang))


@router.delete(
    "/suppliers/{supplier_id}",
    response_model=GenericResponse[None],
    dependencies=[Depends(ScopeGuard(NidusScope.SUPPLIER_WRITE))],
)
async def delete_supplier(
    supplier_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    await SupplierService.delete_supplier(session, supplier_id)
    return GenericResponse(message=i18n.t("success.supplier_deleted", lang=lang))


@router.get(
    "/items",
    response_model=GenericResponse[CursorPage[ItemResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.ITEM_READ))],
)
async def list_items(
    pagination: CursorParams = Depends(),
    filters: ItemFilter = Depends(),
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await ItemService.list_items(session, pagination, filters)
    return GenericResponse(data=data, message=i18n.t("success.items_retrieved", lang=lang))


@router.post(
    "/items",
    response_model=GenericResponse[ItemResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.ITEM_WRITE))],
)
async def create_item(
    data: ItemCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    item = await ItemService.create_item(session, org_id, data)
    return GenericResponse(data=item, message=i18n.t("success.item_created", lang=lang))


@router.get(
    "/items/{item_id}",
    response_model=GenericResponse[ItemResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.ITEM_READ))],
)
async def get_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    item = await ItemService.get_item(session, item_id)
    return GenericResponse(data=item, message=i18n.t("success.item_retrieved", lang=lang))


@router.patch(
    "/items/{item_id}",
    response_model=GenericResponse[ItemResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.ITEM_WRITE))],
)
async def update_item(
    item_id: UUID,
    data: ItemUpdate,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    item = await ItemService.update_item(session, item_id, data)
    return GenericResponse(data=item, message=i18n.t("success.item_updated", lang=lang))


@router.delete(
    "/items/{item_id}",
    response_model=GenericResponse[None],
    dependencies=[Depends(ScopeGuard(NidusScope.ITEM_WRITE))],
)
async def delete_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    await ItemService.delete_item(session, item_id)
    return GenericResponse(message=i18n.t("success.item_deleted", lang=lang))


@router.get(
    "/invoices",
    response_model=GenericResponse[CursorPage[InvoiceListItem]],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def list_invoices(
    pagination: CursorParams = Depends(),
    filters: InvoiceFilter = Depends(),
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await InvoiceService.list_invoices(session, pagination, filters)
    return GenericResponse(data=data, message=i18n.t("success.invoices_retrieved", lang=lang))


@router.post(
    "/invoices",
    response_model=GenericResponse[InvoiceResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def create_invoice(
    data: InvoiceCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    invoice = await InvoiceService.create_invoice(session, org_id, data)
    return GenericResponse(data=invoice, message=i18n.t("success.invoice_created", lang=lang))


@router.get(
    "/invoices/{invoice_id}",
    response_model=GenericResponse[InvoiceResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def get_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await InvoiceService.get_invoice(session, invoice_id)
    return GenericResponse(data=invoice, message=i18n.t("success.invoice_retrieved", lang=lang))


@router.patch(
    "/invoices/{invoice_id}",
    response_model=GenericResponse[InvoiceResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def update_invoice(
    invoice_id: UUID,
    data: InvoiceUpdate,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await InvoiceService.update_invoice(session, invoice_id, data)
    return GenericResponse(data=invoice, message=i18n.t("success.invoice_updated", lang=lang))


@router.delete(
    "/invoices/{invoice_id}",
    response_model=GenericResponse[None],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def delete_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    await InvoiceService.delete_invoice(session, invoice_id)
    return GenericResponse(message=i18n.t("success.invoice_deleted", lang=lang))


@router.post(
    "/invoices/{invoice_id}/issue",
    response_model=GenericResponse[InvoiceResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def issue_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await InvoiceService.issue_invoice(session, invoice_id)
    return GenericResponse(data=invoice, message=i18n.t("success.invoice_issued", lang=lang))


@router.post(
    "/invoices/{invoice_id}/void",
    response_model=GenericResponse[InvoiceResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def void_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await InvoiceService.void_invoice(session, invoice_id)
    return GenericResponse(data=invoice, message=i18n.t("success.invoice_voided", lang=lang))


@router.get(
    "/invoices/{invoice_id}/pdf",
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def download_invoice_pdf(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
):
    pdf = await InvoiceService.render_pdf(session, invoice_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="invoice-{invoice_id}.pdf"'},
    )


@router.get(
    "/invoices/{invoice_id}/payments",
    response_model=GenericResponse[list[InvoicePaymentResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def list_invoice_payments(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await PaymentService.list_payments(session, invoice_id)
    return GenericResponse(data=data, message=i18n.t("success.payments_retrieved", lang=lang))


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=GenericResponse[InvoiceResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def create_invoice_payment(
    invoice_id: UUID,
    data: InvoicePaymentCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await PaymentService.create_payment(session, invoice_id, data)
    return GenericResponse(data=invoice, message=i18n.t("success.payment_created", lang=lang))


@router.delete(
    "/invoices/{invoice_id}/payments/{payment_id}",
    response_model=GenericResponse[InvoiceResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def delete_invoice_payment(
    invoice_id: UUID,
    payment_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    invoice = await PaymentService.delete_payment(session, invoice_id, payment_id)
    return GenericResponse(data=invoice, message=i18n.t("success.payment_deleted", lang=lang))
