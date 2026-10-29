from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import EntityNotFoundError, NidusException
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.enums import InvoiceStatus
from app.models.billing.payment import InvoicePayment
from app.schemas.requests.billing import InvoicePaymentCreate
from app.schemas.responses.billing import InvoicePaymentResponse, InvoiceResponse
from app.services.audit_service import AuditService
from app.services.billing.invoice_service import InvoiceService


class PaymentService:
    @staticmethod
    async def list_payments(session: AsyncSession, invoice_id: UUID) -> list[InvoicePaymentResponse]:
        await InvoiceService._load_invoice(session, invoice_id)
        payments = await InvoiceService._load_payments(session, invoice_id)
        return [InvoicePaymentResponse.model_validate(p) for p in payments]

    @staticmethod
    async def create_payment(
        session: AsyncSession,
        invoice_id: UUID,
        data: InvoicePaymentCreate,
    ) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        if invoice.status in {InvoiceStatus.DRAFT.value, InvoiceStatus.VOID.value, InvoiceStatus.PAID.value}:
            raise NidusException(
                code="INVOICE_NOT_PAYABLE",
                message_key="billing.invoice_not_payable",
                status_code=400,
            )

        amount = InvoiceService._money(data.amount)
        if amount > invoice.balance_due:
            raise NidusException(
                code="PAYMENT_EXCEEDS_BALANCE",
                message_key="billing.payment_exceeds_balance",
                status_code=400,
                balance=str(invoice.balance_due),
            )

        payment = InvoicePayment(
            organization_id=invoice.organization_id,
            invoice_id=invoice.id,
            amount=amount,
            paid_at=data.paid_at or datetime.now(timezone.utc),
            method=data.method.value,
            notes=data.notes,
        )
        session.add(payment)
        invoice.amount_paid = InvoiceService._money(invoice.amount_paid + amount)
        InvoiceService._refresh_payment_status(invoice)

        await AuditService.record(
            session,
            action=AuditAction.INVOICE_PAYMENT_CREATE,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE_PAYMENT,
            resource_id=payment.id,
            details={"invoice_id": str(invoice.id), "amount": str(amount)},
        )
        await session.flush()
        await session.refresh(invoice)
        lines = await InvoiceService._load_lines(session, invoice_id)
        payments = await InvoiceService._load_payments(session, invoice_id)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        response = InvoiceService._to_response(invoice, customer_name, lines, payments)
        await session.commit()
        return response

    @staticmethod
    async def delete_payment(session: AsyncSession, invoice_id: UUID, payment_id: UUID) -> InvoiceResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        if invoice.status == InvoiceStatus.VOID.value:
            raise NidusException(
                code="INVOICE_VOID",
                message_key="billing.invoice_not_payable",
                status_code=400,
            )

        PaymentModel = cast(Any, InvoicePayment)
        stmt = select(InvoicePayment).where(
            PaymentModel.id == payment_id,
            PaymentModel.invoice_id == invoice_id,
        )
        payment = (await session.execute(stmt)).scalar_one_or_none()
        if not payment:
            raise EntityNotFoundError(entity="invoice_payment")

        amount = payment.amount
        await session.delete(payment)
        invoice.amount_paid = InvoiceService._money(max(Decimal("0"), invoice.amount_paid - amount))
        InvoiceService._refresh_payment_status(invoice)

        await AuditService.record(
            session,
            action=AuditAction.INVOICE_PAYMENT_DELETE,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE_PAYMENT,
            resource_id=payment_id,
            details={"invoice_id": str(invoice.id), "amount": str(amount)},
        )
        await session.flush()
        await session.refresh(invoice)
        lines = await InvoiceService._load_lines(session, invoice_id)
        payments = await InvoiceService._load_payments(session, invoice_id)
        customer_name = await InvoiceService._customer_name(session, invoice.customer_id)
        response = InvoiceService._to_response(invoice, customer_name, lines, payments)
        await session.commit()
        return response
