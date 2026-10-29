from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import EntityNotFoundError, NidusException
from app.core.pagination import paginate_with_cursor
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.customer import Customer
from app.models.billing.document_series import DocumentSeries
from app.models.billing.enums import (
    DocumentSeriesType,
    InvoiceStatus,
    PaymentCondition,
    tax_rate_to_mh_code,
)
from app.models.billing.invoice import Invoice, InvoiceLine
from app.models.billing.invoice_fiscal import InvoiceFiscal
from app.models.billing.item import Item
from app.models.billing.payment import InvoicePayment
from app.schemas.filters.billing import InvoiceFilter
from app.schemas.requests.billing import InvoiceCreate, InvoiceLineInput, InvoiceUpdate
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.billing import (
    InvoiceLineResponse,
    InvoiceListItem,
    InvoicePaymentResponse,
    InvoiceResponse,
)
from app.schemas.responses.pagination import CursorPage, PageInfo
from app.services.audit_service import AuditService
from app.services.billing.invoice_pdf import build_invoice_pdf

MONEY = Decimal("0.0001")


class InvoiceService:
    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def _line_amounts(quantity: Decimal, unit_price: Decimal, tax_rate: Decimal | None) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = InvoiceService._money(quantity * unit_price)
        rate = tax_rate if tax_rate is not None else Decimal("0")
        tax = InvoiceService._money(subtotal * (rate / Decimal("100")))
        return subtotal, tax, InvoiceService._money(subtotal + tax)

    @staticmethod
    def _is_overdue(invoice: Invoice) -> bool:
        if invoice.status in {InvoiceStatus.DRAFT.value, InvoiceStatus.VOID.value, InvoiceStatus.PAID.value}:
            return False
        if not invoice.due_date or invoice.balance_due <= 0:
            return False
        return invoice.due_date < date.today()

    @staticmethod
    def _to_line_response(row: InvoiceLine) -> InvoiceLineResponse:
        return InvoiceLineResponse.model_validate(row)

    @staticmethod
    def _to_response(
        invoice: Invoice,
        customer_name: str | None,
        lines: list[InvoiceLine],
        payments: list[InvoicePayment] | None = None,
    ) -> InvoiceResponse:
        return InvoiceResponse(
            id=invoice.id,
            organization_id=invoice.organization_id,
            customer_id=invoice.customer_id,
            customer_name=customer_name,
            payment_condition=invoice.payment_condition,
            status=invoice.status,
            currency=invoice.currency,
            exchange_rate=invoice.exchange_rate,
            exchange_rate_date=invoice.exchange_rate_date,
            document_number=invoice.document_number,
            reference_number=invoice.reference_number,
            notes=invoice.notes,
            issued_at=invoice.issued_at,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_total=invoice.tax_total,
            total=invoice.total,
            amount_paid=invoice.amount_paid,
            balance_due=invoice.balance_due,
            is_overdue=InvoiceService._is_overdue(invoice),
            lines=[InvoiceService._to_line_response(line) for line in lines],
            payments=[InvoicePaymentResponse.model_validate(p) for p in (payments or [])],
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

    @staticmethod
    def _to_list_item(
        invoice: Invoice,
        customer_name: str | None,
        hacienda_status: str | None = None,
    ) -> InvoiceListItem:
        return InvoiceListItem(
            id=invoice.id,
            organization_id=invoice.organization_id,
            customer_id=invoice.customer_id,
            customer_name=customer_name,
            payment_condition=invoice.payment_condition,
            status=invoice.status,
            currency=invoice.currency,
            exchange_rate=invoice.exchange_rate,
            exchange_rate_date=invoice.exchange_rate_date,
            document_number=invoice.document_number,
            reference_number=invoice.reference_number,
            issued_at=invoice.issued_at,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_total=invoice.tax_total,
            total=invoice.total,
            amount_paid=invoice.amount_paid,
            balance_due=invoice.balance_due,
            is_overdue=InvoiceService._is_overdue(invoice),
            hacienda_status=hacienda_status,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

    @staticmethod
    async def _get_customer(session: AsyncSession, org_id: UUID, customer_id: UUID) -> Customer:
        CustomerModel = cast(Any, Customer)
        stmt = select(Customer).where(
            CustomerModel.id == customer_id,
            CustomerModel.organization_id == org_id,
            CustomerModel.deleted_at.is_(None),
        )
        customer = (await session.execute(stmt)).scalar_one_or_none()
        if not customer:
            raise EntityNotFoundError(entity="customer")
        return customer

    @staticmethod
    async def _load_invoice(session: AsyncSession, invoice_id: UUID) -> Invoice:
        InvoiceModel = cast(Any, Invoice)
        stmt = select(Invoice).where(InvoiceModel.id == invoice_id, InvoiceModel.deleted_at.is_(None))
        invoice = (await session.execute(stmt)).scalar_one_or_none()
        if not invoice:
            raise EntityNotFoundError(entity="invoice")
        return invoice

    @staticmethod
    async def _load_lines(session: AsyncSession, invoice_id: UUID) -> list[InvoiceLine]:
        LineModel = cast(Any, InvoiceLine)
        stmt = (
            select(InvoiceLine)
            .where(LineModel.invoice_id == invoice_id)
            .order_by(LineModel.line_number.asc())
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def _load_payments(session: AsyncSession, invoice_id: UUID) -> list[InvoicePayment]:
        PaymentModel = cast(Any, InvoicePayment)
        stmt = (
            select(InvoicePayment)
            .where(PaymentModel.invoice_id == invoice_id)
            .order_by(PaymentModel.paid_at.desc(), PaymentModel.id.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def _allocate_document_number(session: AsyncSession, org_id: UUID) -> str:
        SeriesModel = cast(Any, DocumentSeries)
        stmt = (
            select(DocumentSeries)
            .where(
                SeriesModel.organization_id == org_id,
                SeriesModel.doc_type == DocumentSeriesType.INVOICE.value,
            )
            .with_for_update()
        )
        series = (await session.execute(stmt)).scalar_one_or_none()
        if not series:
            series = DocumentSeries(
                organization_id=org_id,
                doc_type=DocumentSeriesType.INVOICE.value,
                prefix="INV-",
                next_number=1,
                padding=6,
            )
            session.add(series)
            await session.flush()

        number = series.next_number
        series.next_number = number + 1
        return f"{series.prefix}{str(number).zfill(series.padding)}"

    @staticmethod
    def _refresh_payment_status(invoice: Invoice) -> None:
        paid = InvoiceService._money(invoice.amount_paid)
        total = InvoiceService._money(invoice.total)
        invoice.amount_paid = paid
        invoice.balance_due = InvoiceService._money(total - paid)
        if invoice.status == InvoiceStatus.VOID.value:
            return
        if paid <= 0:
            invoice.status = InvoiceStatus.ISSUED.value
        elif paid < total:
            invoice.status = InvoiceStatus.PARTIAL.value
        else:
            invoice.status = InvoiceStatus.PAID.value
            invoice.balance_due = Decimal("0")

    @staticmethod
    async def _customer_name(session: AsyncSession, customer_id: UUID) -> str | None:
        CustomerModel = cast(Any, Customer)
        stmt = select(Customer.name).where(CustomerModel.id == customer_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def _build_lines(
        session: AsyncSession,
        org_id: UUID,
        invoice_id: UUID,
        lines: list[InvoiceLineInput],
    ) -> tuple[list[InvoiceLine], Decimal, Decimal, Decimal]:
        ItemModel = cast(Any, Item)
        built: list[InvoiceLine] = []
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for index, raw in enumerate(lines, start=1):
            description = raw.description.strip()
            sku = raw.sku.strip() if raw.sku else None
            unit = raw.unit.strip() or "unit"
            quantity = raw.quantity
            unit_price = raw.unit_price
            tax_rate = raw.tax_rate
            item_id = raw.item_id

            if item_id:
                item_stmt = select(Item).where(
                    ItemModel.id == item_id,
                    ItemModel.organization_id == org_id,
                    ItemModel.deleted_at.is_(None),
                )
                item = (await session.execute(item_stmt)).scalar_one_or_none()
                if not item:
                    raise EntityNotFoundError(entity="item")
                if not description:
                    description = item.name
                if sku is None:
                    sku = item.sku
                if raw.unit == "unit":
                    unit = item.unit
                if raw.unit_price == Decimal("0") and item.unit_price:
                    unit_price = item.unit_price
                if tax_rate is None:
                    tax_rate = item.tax_rate
                if not raw.cabys_code and item.cabys_code:
                    cabys_from_item = item.cabys_code.strip()
                else:
                    cabys_from_item = None
            else:
                cabys_from_item = None

            line_subtotal, line_tax, line_total = InvoiceService._line_amounts(quantity, unit_price, tax_rate)
            tax_code = (raw.tax_code or tax_rate_to_mh_code(
                float(tax_rate) if tax_rate is not None else None
            )).zfill(2)[:2]
            cabys_code = (raw.cabys_code.strip() if raw.cabys_code else None) or cabys_from_item
            built.append(
                InvoiceLine(
                    organization_id=org_id,
                    invoice_id=invoice_id,
                    line_number=index,
                    item_id=item_id,
                    description=description,
                    sku=sku,
                    unit=unit,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    tax_code=tax_code,
                    cabys_code=cabys_code,
                    line_subtotal=line_subtotal,
                    line_tax=line_tax,
                    line_total=line_total,
                )
            )
            subtotal += line_subtotal
            tax_total += line_tax

        return built, InvoiceService._money(subtotal), InvoiceService._money(tax_total), InvoiceService._money(subtotal + tax_total)

    @staticmethod
    def _assert_draft(invoice: Invoice) -> None:
        if invoice.status != InvoiceStatus.DRAFT.value:
            raise NidusException(
                code="INVOICE_NOT_DRAFT",
                message_key="billing.invoice_not_draft",
                status_code=400,
            )

    @staticmethod
    async def list_invoices(
        session: AsyncSession,
        pagination: CursorParams,
        filters: InvoiceFilter,
    ) -> CursorPage[InvoiceListItem]:
        InvoiceModel = cast(Any, Invoice)
        CustomerModel = cast(Any, Customer)
        stmt = select(Invoice).where(InvoiceModel.deleted_at.is_(None))

        if filters.q:
            term = f"%{filters.q.strip()}%"
            matching_customers = select(CustomerModel.id).where(CustomerModel.name.ilike(term))
            stmt = stmt.where(
                or_(
                    InvoiceModel.reference_number.ilike(term),
                    InvoiceModel.customer_id.in_(matching_customers),
                )
            )
        if filters.status:
            stmt = stmt.where(InvoiceModel.status == filters.status)
        if filters.payment_condition:
            stmt = stmt.where(InvoiceModel.payment_condition == filters.payment_condition)
        if filters.customer_id:
            stmt = stmt.where(InvoiceModel.customer_id == UUID(filters.customer_id))

        rows, end_cursor, has_next = await paginate_with_cursor(
            session=session,
            stmt=stmt,
            model_class=InvoiceModel,
            limit=pagination.limit,
            cursor=pagination.cursor,
        )

        customer_ids = {row.customer_id for row in rows}
        names: dict[UUID, str] = {}
        if customer_ids:
            name_rows = (
                await session.execute(
                    select(CustomerModel.id, CustomerModel.name).where(CustomerModel.id.in_(customer_ids))
                )
            ).all()
            names = {row[0]: row[1] for row in name_rows}

        fiscal_by_invoice: dict[UUID, str] = {}
        invoice_ids = [row.id for row in rows]
        if invoice_ids:
            Fiscal = cast(Any, InvoiceFiscal)
            fiscal_rows = (
                await session.execute(
                    select(Fiscal.invoice_id, Fiscal.status).where(Fiscal.invoice_id.in_(invoice_ids))
                )
            ).all()
            fiscal_by_invoice = {row[0]: row[1] for row in fiscal_rows}

        items = [
            InvoiceService._to_list_item(
                row,
                names.get(row.customer_id),
                fiscal_by_invoice.get(row.id),
            )
            for row in rows
        ]
        return CursorPage(items=items, page_info=PageInfo(has_next_page=has_next, end_cursor=end_cursor))

    @staticmethod
    async def create_invoice(session: AsyncSession, org_id: UUID, data: InvoiceCreate) -> InvoiceResponse:
        customer = await InvoiceService._get_customer(session, org_id, data.customer_id)
        invoice = Invoice(
            organization_id=org_id,
            customer_id=customer.id,
            payment_condition=data.payment_condition.value,
            status=InvoiceStatus.DRAFT.value,
            currency=data.currency.value,
            exchange_rate=data.exchange_rate,
            exchange_rate_date=data.exchange_rate_date,
            reference_number=data.reference_number.strip() if data.reference_number else None,
            notes=data.notes,
            due_date=data.due_date,
        )
        if invoice.currency == "CRC":
            invoice.exchange_rate = None
            invoice.exchange_rate_date = None
        session.add(invoice)
        await session.flush()

        lines, subtotal, tax_total, total = await InvoiceService._build_lines(
            session, org_id, invoice.id, data.lines
        )
        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total = total
        session.add_all(lines)

        await AuditService.record(
            session,
            action=AuditAction.INVOICE_CREATE,
            organization_id=org_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={"customer_id": str(customer.id), "total": str(total)},
        )
        await session.flush()
        await session.refresh(invoice)
        response = InvoiceService._to_response(invoice, customer.name, lines)
        await session.commit()
        return response

    @staticmethod
    async def get_invoice(session: AsyncSession, invoice_id: UUID) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        lines = await InvoiceService._load_lines(session, invoice_id)
        payments = await InvoiceService._load_payments(session, invoice_id)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        return InvoiceService._to_response(invoice, customer_name, lines, payments)

    @staticmethod
    async def update_invoice(session: AsyncSession, invoice_id: UUID, data: InvoiceUpdate) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        InvoiceService._assert_draft(invoice)

        payload = data.model_dump(exclude_unset=True)
        if "customer_id" in payload and payload["customer_id"] is not None:
            customer = await InvoiceService._get_customer(session, invoice.organization_id, payload["customer_id"])
            invoice.customer_id = customer.id
            del payload["customer_id"]
        if "payment_condition" in payload and payload["payment_condition"] is not None:
            condition = payload["payment_condition"]
            invoice.payment_condition = condition.value if isinstance(condition, PaymentCondition) else condition
            del payload["payment_condition"]
        if "reference_number" in payload:
            ref = payload["reference_number"]
            invoice.reference_number = ref.strip() if ref else None
            del payload["reference_number"]
        if "currency" in payload and payload["currency"] is not None:
            currency = payload["currency"]
            invoice.currency = currency.value if hasattr(currency, "value") else str(currency).upper()
            del payload["currency"]
        if "exchange_rate" in payload:
            invoice.exchange_rate = payload.pop("exchange_rate")
        if "exchange_rate_date" in payload:
            invoice.exchange_rate_date = payload.pop("exchange_rate_date")
        if invoice.currency == "CRC":
            invoice.exchange_rate = None
            invoice.exchange_rate_date = None
        for key, value in payload.items():
            if key == "lines":
                continue
            setattr(invoice, key, value)

        lines = await InvoiceService._load_lines(session, invoice_id)
        if data.lines is not None:
            LineModel = cast(Any, InvoiceLine)
            await session.execute(delete(InvoiceLine).where(LineModel.invoice_id == invoice_id))
            lines, subtotal, tax_total, total = await InvoiceService._build_lines(
                session, invoice.organization_id, invoice.id, data.lines
            )
            invoice.subtotal = subtotal
            invoice.tax_total = tax_total
            invoice.total = total
            session.add_all(lines)

        await AuditService.record(
            session,
            action=AuditAction.INVOICE_UPDATE,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={"status": invoice.status, "total": str(invoice.total)},
        )
        await session.flush()
        await session.refresh(invoice)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        response = InvoiceService._to_response(invoice, customer_name, lines)
        await session.commit()
        return response

    @staticmethod
    async def delete_invoice(session: AsyncSession, invoice_id: UUID) -> None:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        InvoiceService._assert_draft(invoice)
        invoice.deleted_at = datetime.now(timezone.utc)
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_DELETE,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={"status": invoice.status},
        )
        await session.commit()

    @staticmethod
    async def issue_invoice(session: AsyncSession, invoice_id: UUID) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        InvoiceService._assert_draft(invoice)
        lines = await InvoiceService._load_lines(session, invoice_id)
        if not lines:
            raise NidusException(
                code="INVOICE_NO_LINES",
                message_key="billing.invoice_no_lines",
                status_code=400,
            )
        if invoice.payment_condition == PaymentCondition.CREDITO.value and not invoice.due_date:
            raise NidusException(
                code="INVOICE_DUE_DATE_REQUIRED",
                message_key="billing.invoice_due_date_required",
                status_code=400,
            )

        invoice.document_number = await InvoiceService._allocate_document_number(
            session, invoice.organization_id
        )
        invoice.status = InvoiceStatus.ISSUED.value
        invoice.issued_at = datetime.now(timezone.utc)
        invoice.amount_paid = Decimal("0")
        invoice.balance_due = InvoiceService._money(invoice.total)
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_ISSUE,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={"total": str(invoice.total), "document_number": invoice.document_number},
        )
        await session.flush()
        await session.refresh(invoice)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        response = InvoiceService._to_response(invoice, customer_name, lines, [])
        await session.commit()
        return response

    @staticmethod
    async def void_invoice(session: AsyncSession, invoice_id: UUID) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        if invoice.status not in {InvoiceStatus.ISSUED.value, InvoiceStatus.PARTIAL.value}:
            raise NidusException(
                code="INVOICE_NOT_ISSUED",
                message_key="billing.invoice_not_issued",
                status_code=400,
            )
        if invoice.amount_paid > 0:
            raise NidusException(
                code="INVOICE_HAS_PAYMENTS",
                message_key="billing.invoice_has_payments",
                status_code=400,
            )
        invoice.status = InvoiceStatus.VOID.value
        lines = await InvoiceService._load_lines(session, invoice_id)
        payments = await InvoiceService._load_payments(session, invoice_id)
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_VOID,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={"total": str(invoice.total), "document_number": invoice.document_number},
        )
        await session.flush()
        await session.refresh(invoice)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        response = InvoiceService._to_response(invoice, customer_name, lines, payments)
        await session.commit()
        return response

    @staticmethod
    async def render_pdf(session: AsyncSession, invoice_id: UUID) -> bytes:
        invoice = await InvoiceService.get_invoice(session, invoice_id)
        return build_invoice_pdf(invoice)
