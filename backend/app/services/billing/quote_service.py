from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import EntityNotFoundError, NidusException
from app.core.pagination import paginate_with_cursor
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.customer import Customer
from app.models.billing.enums import (
    InvoiceCurrency,
    PaymentCondition,
    QuoteStatus,
    tax_rate_to_mh_code,
)
from app.models.billing.invoice import Invoice
from app.models.billing.item import Item
from app.models.billing.quote import Quote, QuoteLine
from app.schemas.filters.billing import QuoteFilter
from app.schemas.requests.billing import (
    InvoiceLineInput,
    QuoteCreate,
    QuoteUpdate,
)
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.billing import (
    InvoiceResponse,
    QuoteLineResponse,
    QuoteListItem,
    QuoteResponse,
)
from app.schemas.responses.pagination import CursorPage, PageInfo
from app.services.audit_service import AuditService
from app.services.billing.invoice_service import InvoiceService


class QuoteService:
    @staticmethod
    def _to_line_response(row: QuoteLine) -> QuoteLineResponse:
        return QuoteLineResponse.model_validate(row)

    @staticmethod
    def _to_response(
        quote: Quote,
        customer_name: str | None,
        lines: list[QuoteLine],
    ) -> QuoteResponse:
        return QuoteResponse(
            id=quote.id,
            organization_id=quote.organization_id,
            customer_id=quote.customer_id,
            customer_name=customer_name,
            status=quote.status,
            currency=quote.currency,
            exchange_rate=quote.exchange_rate,
            exchange_rate_date=quote.exchange_rate_date,
            reference_number=quote.reference_number,
            notes=quote.notes,
            valid_until=quote.valid_until,
            subtotal=quote.subtotal,
            tax_total=quote.tax_total,
            total=quote.total,
            converted_invoice_id=quote.converted_invoice_id,
            lines=[QuoteService._to_line_response(line) for line in lines],
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )

    @staticmethod
    def _to_list_item(quote: Quote, customer_name: str | None) -> QuoteListItem:
        return QuoteListItem(
            id=quote.id,
            organization_id=quote.organization_id,
            customer_id=quote.customer_id,
            customer_name=customer_name,
            status=quote.status,
            currency=quote.currency,
            exchange_rate=quote.exchange_rate,
            exchange_rate_date=quote.exchange_rate_date,
            reference_number=quote.reference_number,
            valid_until=quote.valid_until,
            subtotal=quote.subtotal,
            tax_total=quote.tax_total,
            total=quote.total,
            converted_invoice_id=quote.converted_invoice_id,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )

    @staticmethod
    async def _load_quote(session: AsyncSession, quote_id: UUID) -> Quote:
        QuoteModel = cast(Any, Quote)
        stmt = select(Quote).where(QuoteModel.id == quote_id, QuoteModel.deleted_at.is_(None))
        quote = (await session.execute(stmt)).scalar_one_or_none()
        if not quote:
            raise EntityNotFoundError(entity="quote")
        return quote

    @staticmethod
    async def _load_lines(session: AsyncSession, quote_id: UUID) -> list[QuoteLine]:
        LineModel = cast(Any, QuoteLine)
        stmt = (
            select(QuoteLine)
            .where(LineModel.quote_id == quote_id)
            .order_by(LineModel.line_number.asc())
        )
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    def _assert_editable(quote: Quote) -> None:
        if quote.status == QuoteStatus.CONVERTED.value:
            raise NidusException(
                code="QUOTE_ALREADY_CONVERTED",
                message_key="billing.quote_already_converted",
                status_code=409,
            )
        if quote.status not in {
            QuoteStatus.DRAFT.value,
            QuoteStatus.SENT.value,
            QuoteStatus.ACCEPTED.value,
        }:
            raise NidusException(
                code="QUOTE_NOT_EDITABLE",
                message_key="billing.quote_not_editable",
                status_code=400,
            )

    @staticmethod
    async def _replace_lines(
        session: AsyncSession,
        org_id: UUID,
        quote_id: UUID,
        lines: list[InvoiceLineInput],
    ) -> tuple[list[QuoteLine], Decimal, Decimal, Decimal]:
        LineModel = cast(Any, QuoteLine)
        ItemModel = cast(Any, Item)
        await session.execute(delete(QuoteLine).where(LineModel.quote_id == quote_id))

        built: list[QuoteLine] = []
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
            cabys_from_item = None

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

            line_subtotal, line_tax, line_total = InvoiceService._line_amounts(
                quantity, unit_price, tax_rate
            )
            tax_code = (
                raw.tax_code
                or tax_rate_to_mh_code(float(tax_rate) if tax_rate is not None else None)
            ).zfill(2)[:2]
            cabys_code = (raw.cabys_code.strip() if raw.cabys_code else None) or cabys_from_item
            built.append(
                QuoteLine(
                    organization_id=org_id,
                    quote_id=quote_id,
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

        session.add_all(built)
        return (
            built,
            InvoiceService._money(subtotal),
            InvoiceService._money(tax_total),
            InvoiceService._money(subtotal + tax_total),
        )

    @staticmethod
    async def list_quotes(
        session: AsyncSession,
        pagination: CursorParams,
        filters: QuoteFilter,
    ) -> CursorPage[QuoteListItem]:
        QuoteModel = cast(Any, Quote)
        CustomerModel = cast(Any, Customer)
        stmt = select(Quote).where(QuoteModel.deleted_at.is_(None))

        if filters.q:
            term = f"%{filters.q.strip()}%"
            matching_customers = select(CustomerModel.id).where(CustomerModel.name.ilike(term))
            stmt = stmt.where(
                or_(
                    QuoteModel.reference_number.ilike(term),
                    QuoteModel.customer_id.in_(matching_customers),
                )
            )
        if filters.status:
            stmt = stmt.where(QuoteModel.status == filters.status)
        if filters.customer_id:
            stmt = stmt.where(QuoteModel.customer_id == UUID(filters.customer_id))

        rows, end_cursor, has_next = await paginate_with_cursor(
            session=session,
            stmt=stmt,
            model_class=QuoteModel,
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

        items = [QuoteService._to_list_item(row, names.get(row.customer_id)) for row in rows]
        return CursorPage(items=items, page_info=PageInfo(has_next_page=has_next, end_cursor=end_cursor))

    @staticmethod
    async def create_quote(session: AsyncSession, org_id: UUID, data: QuoteCreate) -> QuoteResponse:
        customer = await InvoiceService._get_customer(session, org_id, data.customer_id)
        quote = Quote(
            organization_id=org_id,
            customer_id=customer.id,
            status=QuoteStatus.DRAFT.value,
            currency=data.currency.value,
            exchange_rate=data.exchange_rate,
            exchange_rate_date=data.exchange_rate_date,
            reference_number=data.reference_number.strip() if data.reference_number else None,
            notes=data.notes,
            valid_until=data.valid_until,
        )
        if quote.currency == "CRC":
            quote.exchange_rate = None
            quote.exchange_rate_date = None
        session.add(quote)
        await session.flush()

        lines, subtotal, tax_total, total = await QuoteService._replace_lines(
            session, org_id, quote.id, data.lines
        )
        quote.subtotal = subtotal
        quote.tax_total = tax_total
        quote.total = total

        await AuditService.record(
            session,
            action=AuditAction.QUOTE_CREATE,
            organization_id=org_id,
            resource_type=AuditResourceType.QUOTE,
            resource_id=quote.id,
            details={"customer_id": str(customer.id), "total": str(total)},
        )
        await session.flush()
        await session.refresh(quote)
        response = QuoteService._to_response(quote, customer.name, lines)
        await session.commit()
        return response

    @staticmethod
    async def get_quote(session: AsyncSession, quote_id: UUID) -> QuoteResponse:
        quote = await QuoteService._load_quote(session, quote_id)
        lines = await QuoteService._load_lines(session, quote_id)
        customer_name = await InvoiceService._customer_name(session, quote.customer_id)
        return QuoteService._to_response(quote, customer_name, lines)

    @staticmethod
    async def update_quote(session: AsyncSession, quote_id: UUID, data: QuoteUpdate) -> QuoteResponse:
        quote = await QuoteService._load_quote(session, quote_id)
        QuoteService._assert_editable(quote)
        if quote.status == QuoteStatus.SENT.value:
            # allow edits while sent; keep status
            pass

        payload = data.model_dump(exclude_unset=True)
        if "customer_id" in payload and payload["customer_id"] is not None:
            customer = await InvoiceService._get_customer(
                session, quote.organization_id, payload["customer_id"]
            )
            quote.customer_id = customer.id
            del payload["customer_id"]
        if "currency" in payload and payload["currency"] is not None:
            currency = payload["currency"]
            quote.currency = currency.value if isinstance(currency, InvoiceCurrency) else currency
            del payload["currency"]
        if "reference_number" in payload:
            ref = payload.pop("reference_number")
            quote.reference_number = ref.strip() if isinstance(ref, str) and ref.strip() else None
        if "notes" in payload:
            quote.notes = payload.pop("notes")
        if "valid_until" in payload:
            quote.valid_until = payload.pop("valid_until")
        if "exchange_rate" in payload:
            quote.exchange_rate = payload.pop("exchange_rate")
        if "exchange_rate_date" in payload:
            quote.exchange_rate_date = payload.pop("exchange_rate_date")

        lines_input = payload.pop("lines", None)
        if quote.currency == "CRC":
            quote.exchange_rate = None
            quote.exchange_rate_date = None

        if lines_input is not None:
            lines, subtotal, tax_total, total = await QuoteService._replace_lines(
                session, quote.organization_id, quote.id, lines_input
            )
            quote.subtotal = subtotal
            quote.tax_total = tax_total
            quote.total = total
        else:
            lines = await QuoteService._load_lines(session, quote.id)

        await AuditService.record(
            session,
            action=AuditAction.QUOTE_UPDATE,
            organization_id=quote.organization_id,
            resource_type=AuditResourceType.QUOTE,
            resource_id=quote.id,
            details={"status": quote.status},
        )
        await session.flush()
        await session.refresh(quote)
        customer_name = await InvoiceService._customer_name(session, quote.customer_id)
        response = QuoteService._to_response(quote, customer_name, lines)
        await session.commit()
        return response

    @staticmethod
    async def delete_quote(session: AsyncSession, quote_id: UUID) -> None:
        quote = await QuoteService._load_quote(session, quote_id)
        if quote.status == QuoteStatus.CONVERTED.value:
            raise NidusException(
                code="QUOTE_ALREADY_CONVERTED",
                message_key="billing.quote_already_converted",
                status_code=409,
            )
        quote.deleted_at = datetime.now(timezone.utc)
        await AuditService.record(
            session,
            action=AuditAction.QUOTE_DELETE,
            organization_id=quote.organization_id,
            resource_type=AuditResourceType.QUOTE,
            resource_id=quote.id,
        )
        await session.commit()

    @staticmethod
    async def mark_sent(session: AsyncSession, quote_id: UUID) -> QuoteResponse:
        quote = await QuoteService._load_quote(session, quote_id)
        if quote.status == QuoteStatus.CONVERTED.value:
            raise NidusException(
                code="QUOTE_ALREADY_CONVERTED",
                message_key="billing.quote_already_converted",
                status_code=409,
            )
        if quote.status not in {QuoteStatus.DRAFT.value, QuoteStatus.SENT.value}:
            raise NidusException(
                code="QUOTE_NOT_SENDABLE",
                message_key="billing.quote_not_sendable",
                status_code=400,
            )
        quote.status = QuoteStatus.SENT.value
        await AuditService.record(
            session,
            action=AuditAction.QUOTE_SEND,
            organization_id=quote.organization_id,
            resource_type=AuditResourceType.QUOTE,
            resource_id=quote.id,
        )
        await session.flush()
        await session.refresh(quote)
        lines = await QuoteService._load_lines(session, quote.id)
        customer_name = await InvoiceService._customer_name(session, quote.customer_id)
        response = QuoteService._to_response(quote, customer_name, lines)
        await session.commit()
        return response

    @staticmethod
    async def convert_to_invoice(session: AsyncSession, quote_id: UUID) -> InvoiceResponse:
        quote = await QuoteService._load_quote(session, quote_id)
        if quote.status == QuoteStatus.CONVERTED.value:
            raise NidusException(
                code="QUOTE_ALREADY_CONVERTED",
                message_key="billing.quote_already_converted",
                status_code=409,
            )
        if quote.status == QuoteStatus.REJECTED.value:
            raise NidusException(
                code="QUOTE_NOT_CONVERTIBLE",
                message_key="billing.quote_not_convertible",
                status_code=400,
            )

        quote_lines = await QuoteService._load_lines(session, quote.id)
        if not quote_lines:
            raise NidusException(
                code="QUOTE_EMPTY",
                message_key="billing.quote_empty",
                status_code=400,
            )

        customer = await InvoiceService._get_customer(
            session, quote.organization_id, quote.customer_id
        )
        invoice = Invoice(
            organization_id=quote.organization_id,
            customer_id=quote.customer_id,
            payment_condition=PaymentCondition.CONTADO.value,
            status="draft",
            currency=quote.currency,
            exchange_rate=quote.exchange_rate if quote.currency != "CRC" else None,
            exchange_rate_date=quote.exchange_rate_date if quote.currency != "CRC" else None,
            reference_number=quote.reference_number,
            notes=quote.notes,
        )
        session.add(invoice)
        await session.flush()

        line_inputs = [
            InvoiceLineInput(
                item_id=line.item_id,
                description=line.description,
                sku=line.sku,
                unit=line.unit,
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax_rate=line.tax_rate,
                tax_code=line.tax_code,
                cabys_code=line.cabys_code,
            )
            for line in quote_lines
        ]
        invoice_lines, subtotal, tax_total, total = await InvoiceService._build_lines(
            session, quote.organization_id, invoice.id, line_inputs
        )
        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total = total
        session.add_all(invoice_lines)

        quote.status = QuoteStatus.CONVERTED.value
        quote.converted_invoice_id = invoice.id

        await AuditService.record(
            session,
            action=AuditAction.INVOICE_CREATE,
            organization_id=quote.organization_id,
            resource_type=AuditResourceType.INVOICE,
            resource_id=invoice.id,
            details={
                "customer_id": str(quote.customer_id),
                "total": str(total),
                "from_quote_id": str(quote.id),
            },
        )
        await AuditService.record(
            session,
            action=AuditAction.QUOTE_CONVERT,
            organization_id=quote.organization_id,
            resource_type=AuditResourceType.QUOTE,
            resource_id=quote.id,
            details={"invoice_id": str(invoice.id)},
        )
        await session.flush()
        await session.refresh(invoice)
        response = InvoiceService._to_response(invoice, customer.name, invoice_lines)
        await session.commit()
        return response
