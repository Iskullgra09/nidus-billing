from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ScopeGuard, get_current_tenant_session, get_jwt_payload, get_language
from app.core.exceptions.base import AuthenticationError
from app.core.i18n.service import i18n
from app.core.rate_limit import RateLimit
from app.core.request_context import RequestContext
from app.models.billing.enums import HaciendaEnvironment
from app.models.identity.scopes import NidusScope
from app.schemas.filters.billing import InboundFilter, InvoiceFilter, ItemFilter, PartyFilter
from app.schemas.requests.billing import (
    FiscalProfileUpsert,
    HaciendaCredentialUpsert,
    InboundDocumentCreate,
    InboundDocumentLink,
    InboundMailboxUpdate,
    InboundRejectRequest,
    InvoiceCreate,
    InvoicePaymentCreate,
    InvoiceSendEmail,
    InvoiceUpdate,
    ItemCreate,
    ItemUpdate,
    PartyCreate,
    PartyUpdate,
)
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.base import GenericResponse
from app.schemas.responses.billing import (
    FiscalProfileResponse,
    HaciendaCredentialStatusResponse,
    InboundDocumentResponse,
    InboundMailboxResponse,
    InvoiceEmailDeliveryResponse,
    InvoiceFiscalResponse,
    InvoiceListItem,
    InvoicePaymentResponse,
    InvoiceResponse,
    ItemResponse,
    PartyResponse,
)
from app.schemas.responses.pagination import CursorPage
from app.services.billing import (
    CustomerService,
    FiscalService,
    HaciendaEmitService,
    HaciendaInboundService,
    InboundMailboxService,
    InvoiceEmailService,
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
    "/invoices/{invoice_id}/fiscal",
    response_model=GenericResponse[Optional[InvoiceFiscalResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def get_invoice_fiscal(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await HaciendaEmitService.get_for_invoice(session, invoice_id)
    return GenericResponse(
        data=data,
        message=i18n.t("success.invoice_fiscal_retrieved", lang=lang),
    )


@router.post(
    "/invoices/{invoice_id}/emit-hacienda",
    response_model=GenericResponse[InvoiceFiscalResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INVOICE_WRITE)),
        Depends(RateLimit("billing.invoice_emit", tier="strict")),
    ],
)
async def emit_invoice_hacienda(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaEmitService.emit(session, org_id, invoice_id)
    return GenericResponse(data=data, message=i18n.t("success.invoice_fiscal_emitted", lang=lang))


@router.post(
    "/invoices/{invoice_id}/verify-hacienda",
    response_model=GenericResponse[InvoiceFiscalResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INVOICE_WRITE)),
        Depends(RateLimit("billing.invoice_verify", tier="strict")),
    ],
)
async def verify_invoice_hacienda(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaEmitService.verify(session, org_id, invoice_id)
    return GenericResponse(data=data, message=i18n.t("success.invoice_fiscal_verified", lang=lang))


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


@router.get(
    "/invoices/{invoice_id}/emails",
    response_model=GenericResponse[list[InvoiceEmailDeliveryResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_READ))],
)
async def list_invoice_emails(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await InvoiceEmailService.list_deliveries(session, invoice_id)
    return GenericResponse(data=data, message=i18n.t("success.invoice_emails_retrieved", lang=lang))


@router.post(
    "/invoices/{invoice_id}/send-email",
    response_model=GenericResponse[InvoiceEmailDeliveryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ScopeGuard(NidusScope.INVOICE_WRITE))],
)
async def send_invoice_email(
    invoice_id: UUID,
    data: InvoiceSendEmail,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    actor_raw = payload.get("sub")
    actor_user_id = UUID(str(actor_raw)) if actor_raw else None
    delivery = await InvoiceEmailService.send_invoice_email(
        session,
        invoice_id,
        data,
        actor_user_id=actor_user_id,
        lang=lang,
    )
    return GenericResponse(data=delivery, message=i18n.t("success.invoice_email_sent", lang=lang))


@router.get(
    "/fiscal-profile",
    response_model=GenericResponse[Optional[FiscalProfileResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.FISCAL_READ))],
)
async def get_fiscal_profile(
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await FiscalService.get_profile(session, org_id)
    return GenericResponse(data=data, message=i18n.t("success.fiscal_profile_retrieved", lang=lang))


@router.put(
    "/fiscal-profile",
    response_model=GenericResponse[FiscalProfileResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.FISCAL_WRITE))],
)
async def upsert_fiscal_profile(
    data: FiscalProfileUpsert,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    profile = await FiscalService.upsert_profile(session, org_id, data)
    return GenericResponse(data=profile, message=i18n.t("success.fiscal_profile_updated", lang=lang))


@router.get(
    "/hacienda-credentials",
    response_model=GenericResponse[HaciendaCredentialStatusResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.FISCAL_READ))],
)
async def get_hacienda_credentials(
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await FiscalService.get_credential_status(session, org_id)
    return GenericResponse(
        data=data,
        message=i18n.t("success.hacienda_credentials_retrieved", lang=lang),
    )


@router.put(
    "/hacienda-credentials",
    response_model=GenericResponse[HaciendaCredentialStatusResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.FISCAL_WRITE)),
        Depends(RateLimit("billing.hacienda_credentials", tier="strict")),
    ],
)
async def upsert_hacienda_credentials(
    environment: HaciendaEnvironment = Form(default=HaciendaEnvironment.SANDBOX),
    username: Optional[str] = Form(default=None),
    p12_password: Optional[str] = Form(default=None),
    pin: Optional[str] = Form(default=None),
    oauth_client_id: Optional[str] = Form(default=None),
    oauth_client_secret: Optional[str] = Form(default=None),
    p12_file: Optional[UploadFile] = File(default=None),
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    p12_bytes: Optional[bytes] = None
    if p12_file is not None and p12_file.filename:
        p12_bytes = await p12_file.read()
    data = HaciendaCredentialUpsert(
        environment=environment,
        username=username,
        p12_password=p12_password,
        pin=pin,
        oauth_client_id=oauth_client_id,
        oauth_client_secret=oauth_client_secret,
    )
    status_payload = await FiscalService.upsert_credentials(
        session,
        org_id,
        data,
        p12_bytes=p12_bytes,
    )
    return GenericResponse(
        data=status_payload,
        message=i18n.t("success.hacienda_credentials_updated", lang=lang),
    )


@router.delete(
    "/hacienda-credentials",
    response_model=GenericResponse[HaciendaCredentialStatusResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.FISCAL_WRITE))],
)
async def delete_hacienda_credentials(
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await FiscalService.delete_credentials(session, org_id)
    return GenericResponse(
        data=data,
        message=i18n.t("success.hacienda_credentials_deleted", lang=lang),
    )


def _actor_user_id(payload: dict[str, Any]) -> UUID:
    actor_raw = payload.get("sub")
    if not actor_raw:
        raise AuthenticationError()
    return UUID(str(actor_raw))


@router.get(
    "/inbound-mailbox",
    response_model=GenericResponse[InboundMailboxResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INBOUND_READ))],
)
async def get_inbound_mailbox(
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await InboundMailboxService.get_or_provision(
        session,
        org_id,
        actor_user_id=_actor_user_id(payload),
        ip_address=RequestContext.get_client_ip(),
    )
    return GenericResponse(
        data=data,
        message=i18n.t("success.inbound_mailbox_retrieved", lang=lang),
    )


@router.put(
    "/inbound-mailbox",
    response_model=GenericResponse[InboundMailboxResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INBOUND_WRITE)),
        Depends(RateLimit("billing.inbound_mailbox", tier="moderate")),
    ],
)
async def update_inbound_mailbox(
    body: InboundMailboxUpdate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await InboundMailboxService.update(
        session,
        org_id,
        body,
        actor_user_id=_actor_user_id(payload),
        ip_address=RequestContext.get_client_ip(),
    )
    return GenericResponse(
        data=data,
        message=i18n.t("success.inbound_mailbox_updated", lang=lang),
    )


@router.get(
    "/inbound-documents",
    response_model=GenericResponse[CursorPage[InboundDocumentResponse]],
    dependencies=[Depends(ScopeGuard(NidusScope.INBOUND_READ))],
)
async def list_inbound_documents(
    pagination: CursorParams = Depends(),
    filters: InboundFilter = Depends(),
    session: AsyncSession = Depends(get_current_tenant_session),
    lang: str = Depends(get_language),
):
    data = await HaciendaInboundService.list_documents(session, pagination, filters)
    return GenericResponse(data=data, message=i18n.t("success.inbound_list", lang=lang))


@router.get(
    "/inbound-documents/{document_id}",
    response_model=GenericResponse[InboundDocumentResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INBOUND_READ))],
)
async def get_inbound_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.get_document(session, org_id, document_id)
    return GenericResponse(data=data, message=i18n.t("success.inbound_retrieved", lang=lang))


@router.post(
    "/inbound-documents",
    response_model=GenericResponse[InboundDocumentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(ScopeGuard(NidusScope.INBOUND_WRITE)),
        Depends(RateLimit("billing.inbound_create", tier="strict")),
    ],
)
async def create_inbound_document(
    body: InboundDocumentCreate,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.create_from_xml(
        session,
        org_id,
        body,
        actor_user_id=_actor_user_id(payload),
        ip_address=None,
    )
    return GenericResponse(data=data, message=i18n.t("success.inbound_created", lang=lang))


@router.patch(
    "/inbound-documents/{document_id}",
    response_model=GenericResponse[InboundDocumentResponse],
    dependencies=[Depends(ScopeGuard(NidusScope.INBOUND_WRITE))],
)
async def link_inbound_document(
    document_id: UUID,
    body: InboundDocumentLink,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.link_supplier(
        session,
        org_id,
        document_id,
        body,
        actor_user_id=_actor_user_id(payload),
        ip_address=None,
    )
    return GenericResponse(data=data, message=i18n.t("success.inbound_linked", lang=lang))


@router.post(
    "/inbound-documents/{document_id}/accept-hacienda",
    response_model=GenericResponse[InboundDocumentResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INBOUND_WRITE)),
        Depends(RateLimit("billing.inbound_accept", tier="strict")),
    ],
)
async def accept_inbound_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.accept(
        session,
        org_id,
        document_id,
        actor_user_id=_actor_user_id(payload),
        ip_address=None,
    )
    return GenericResponse(data=data, message=i18n.t("success.inbound_accepted", lang=lang))


@router.post(
    "/inbound-documents/{document_id}/reject-hacienda",
    response_model=GenericResponse[InboundDocumentResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INBOUND_WRITE)),
        Depends(RateLimit("billing.inbound_reject", tier="strict")),
    ],
)
async def reject_inbound_document(
    document_id: UUID,
    body: InboundRejectRequest,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.reject(
        session,
        org_id,
        document_id,
        reason=body.reason,
        actor_user_id=_actor_user_id(payload),
        ip_address=None,
    )
    return GenericResponse(data=data, message=i18n.t("success.inbound_rejected", lang=lang))


@router.post(
    "/inbound-documents/{document_id}/verify-hacienda",
    response_model=GenericResponse[InboundDocumentResponse],
    dependencies=[
        Depends(ScopeGuard(NidusScope.INBOUND_WRITE)),
        Depends(RateLimit("billing.inbound_verify", tier="strict")),
    ],
)
async def verify_inbound_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_current_tenant_session),
    payload: dict[str, Any] = Depends(get_jwt_payload),
    lang: str = Depends(get_language),
):
    org_id = _require_org_id(payload)
    data = await HaciendaInboundService.verify(
        session,
        org_id,
        document_id,
        actor_user_id=_actor_user_id(payload),
        ip_address=None,
    )
    return GenericResponse(data=data, message=i18n.t("success.inbound_verified", lang=lang))
