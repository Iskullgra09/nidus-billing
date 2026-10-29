from datetime import datetime, timezone
from decimal import Decimal
from html import escape
from typing import Any, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import NidusException
from app.core.i18n.service import i18n
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.customer import Customer
from app.models.billing.enums import InvoiceEmailStatus, InvoiceStatus
from app.models.billing.invoice_email import InvoiceEmailDelivery
from app.schemas.requests.billing import InvoiceSendEmail
from app.schemas.responses.billing import InvoiceEmailDeliveryResponse
from app.services.audit_service import AuditService
from app.services.billing.invoice_service import InvoiceService
from app.services.email_service import EmailService


def _format_email_amount(value: Decimal, currency: str) -> str:
    quantized = value.quantize(Decimal("0.01"))
    return f"{quantized:,.2f} {currency}"


def _build_invoice_email_html(
    *,
    lang: str,
    customer_name: str,
    document_number: str,
    amount_label: str,
    optional_message: Optional[str],
) -> str:
    greeting = i18n.t(
        "email.invoice_greeting",
        lang=lang,
        customer_name=escape(customer_name),
    )
    intro = i18n.t(
        "email.invoice_intro",
        lang=lang,
        document_number=escape(document_number),
    )
    amount_caption = i18n.t("email.invoice_amount_label", lang=lang)
    attachment_note = i18n.t("email.invoice_attachment_note", lang=lang)
    footer = i18n.t("email.invoice_footer", lang=lang)
    extra = ""
    if optional_message:
        extra = (
            '<p style="margin:20px 0 0;padding:14px 16px;background:#fafafa;'
            'border-left:3px solid #18181b;color:#3f3f46;font-size:14px;'
            f'line-height:1.5;">{escape(optional_message)}</p>'
        )

    brand = (
        "font-family:Arial,Helvetica,sans-serif;font-size:11px;"
        "letter-spacing:0.14em;text-transform:uppercase;color:#71717a;"
    )
    title = (
        "font-family:Arial,Helvetica,sans-serif;font-size:22px;"
        "font-weight:700;color:#18181b;margin-top:10px;"
    )
    body = (
        "padding:28px 32px;font-family:Arial,Helvetica,sans-serif;"
        "font-size:15px;line-height:1.6;color:#3f3f46;"
    )
    amount_cap = (
        "font-size:11px;letter-spacing:0.08em;"
        "text-transform:uppercase;color:#71717a;"
    )
    amount_val = (
        "font-size:24px;font-weight:700;color:#18181b;margin-top:6px;"
    )
    foot = (
        "padding:16px 32px;background:#fafafa;border-top:1px solid #e4e4e7;"
        "font-family:Arial,Helvetica,sans-serif;font-size:12px;"
        "line-height:1.5;color:#a1a1aa;"
    )
    wrap = "background:#f4f4f5;padding:32px 12px;"
    card = "max-width:560px;width:100%;background:#ffffff;border:1px solid #e4e4e7;"
    box = "background:#fafafa;border:1px solid #e4e4e7;"
    doc = escape(document_number)
    amt_cap = escape(amount_caption)
    amt_val = escape(amount_label)
    note = escape(attachment_note)
    foot_txt = escape(footer)

    return f"""<!DOCTYPE html>
<html lang="{escape(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
</head>
<body style="margin:0;padding:0;background:#f4f4f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
    style="{wrap}">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0"
        style="{card}">
        <tr>
          <td style="padding:28px 32px 20px;border-bottom:3px solid #18181b;">
            <div style="{brand}">Nidus Billing</div>
            <div style="{title}">{doc}</div>
          </td>
        </tr>
        <tr>
          <td style="{body}">
            <p style="margin:0 0 16px;">{greeting}</p>
            <p style="margin:0 0 24px;">{intro}</p>
            <table role="presentation" width="100%" cellpadding="0"
              cellspacing="0" style="{box}">
              <tr>
                <td style="padding:16px 20px;">
                  <div style="{amount_cap}">{amt_cap}</div>
                  <div style="{amount_val}">{amt_val}</div>
                </td>
              </tr>
            </table>
            {extra}
            <p style="margin:24px 0 0;font-size:14px;color:#52525b;">{note}</p>
          </td>
        </tr>
        <tr>
          <td style="{foot}">
            {foot_txt}
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


class InvoiceEmailService:
    @staticmethod
    def _to_response(row: InvoiceEmailDelivery) -> InvoiceEmailDeliveryResponse:
        return InvoiceEmailDeliveryResponse.model_validate(row)

    @staticmethod
    async def list_deliveries(
        session: AsyncSession,
        invoice_id: UUID,
    ) -> list[InvoiceEmailDeliveryResponse]:
        await InvoiceService._load_invoice(session, invoice_id)
        Delivery = cast(Any, InvoiceEmailDelivery)
        stmt = (
            select(InvoiceEmailDelivery)
            .where(Delivery.invoice_id == invoice_id)
            .order_by(Delivery.created_at.desc(), Delivery.id.desc())
        )
        rows = list((await session.execute(stmt)).scalars().all())
        return [InvoiceEmailService._to_response(row) for row in rows]

    @staticmethod
    async def send_invoice_email(
        session: AsyncSession,
        invoice_id: UUID,
        data: InvoiceSendEmail,
        *,
        actor_user_id: Optional[UUID],
        lang: str = "en",
    ) -> InvoiceEmailDeliveryResponse:
        invoice = await InvoiceService._load_invoice(session, invoice_id)
        if invoice.status in {InvoiceStatus.DRAFT.value, InvoiceStatus.VOID.value}:
            raise NidusException(
                code="INVOICE_NOT_EMAILABLE",
                message_key="billing.invoice_not_emailable",
                status_code=400,
            )

        CustomerModel = cast(Any, Customer)
        customer = (
            await session.execute(select(Customer).where(CustomerModel.id == invoice.customer_id))
        ).scalar_one_or_none()
        if not customer:
            raise NidusException(
                code="CUSTOMER_NOT_FOUND",
                message_key="common.not_found",
                status_code=404,
            )

        to_email = str(data.to_email).strip() if data.to_email else (customer.email or "").strip()
        if not to_email:
            raise NidusException(
                code="INVOICE_EMAIL_REQUIRED",
                message_key="billing.invoice_email_required",
                status_code=400,
            )

        doc_label = invoice.document_number or invoice.reference_number or str(invoice.id)[:8]
        amount_label = _format_email_amount(Decimal(invoice.total), invoice.currency)
        optional_message = data.message.strip() if data.message and data.message.strip() else None
        subject = data.subject.strip() if data.subject else i18n.t(
            "email.invoice_subject",
            lang=lang,
            document_number=doc_label,
        )
        body_text = i18n.t(
            "email.invoice_body",
            lang=lang,
            document_number=doc_label,
            customer_name=customer.name,
            total=amount_label,
        )
        if optional_message:
            body_text = f"{body_text}\n\n{optional_message}"

        body_html = _build_invoice_email_html(
            lang=lang,
            customer_name=customer.name,
            document_number=doc_label,
            amount_label=amount_label,
            optional_message=optional_message,
        )

        pdf_bytes = await InvoiceService.render_pdf(session, invoice_id)
        pdf_name = f"{doc_label}.pdf".replace("/", "-")

        delivery = InvoiceEmailDelivery(
            organization_id=invoice.organization_id,
            invoice_id=invoice.id,
            to_email=to_email,
            subject=subject,
            status=InvoiceEmailStatus.FAILED.value,
            actor_user_id=actor_user_id,
        )
        session.add(delivery)

        try:
            result = await EmailService.send_invoice_email(
                to_email=to_email,
                subject=subject,
                text_content=body_text,
                html_content=body_html,
                pdf_bytes=pdf_bytes,
                pdf_filename=pdf_name,
            )
            delivery.status = (
                InvoiceEmailStatus.MOCKED.value
                if result == "mocked"
                else InvoiceEmailStatus.SENT.value
            )
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.error_message = None
        except Exception as exc:
            delivery.status = InvoiceEmailStatus.FAILED.value
            delivery.error_message = str(exc)[:2000]
            delivery.sent_at = None
            await session.flush()
            await AuditService.record(
                session,
                action=AuditAction.INVOICE_EMAIL_SEND,
                organization_id=invoice.organization_id,
                resource_type=AuditResourceType.INVOICE_EMAIL,
                resource_id=delivery.id,
                details={
                    "invoice_id": str(invoice.id),
                    "to_email": to_email,
                    "status": delivery.status,
                    "error": delivery.error_message,
                },
            )
            await session.commit()
            raise NidusException(
                code="INVOICE_EMAIL_FAILED",
                message_key="billing.invoice_email_failed",
                status_code=502,
                error=str(exc)[:200],
            ) from exc

        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_EMAIL_SEND,
            organization_id=invoice.organization_id,
            resource_type=AuditResourceType.INVOICE_EMAIL,
            resource_id=delivery.id,
            details={
                "invoice_id": str(invoice.id),
                "to_email": to_email,
                "status": delivery.status,
            },
        )
        await session.refresh(delivery)
        response = InvoiceEmailService._to_response(delivery)
        await session.commit()
        return response
