from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.base import EntityNotFoundError, NidusException
from app.core.field_encryption import decrypt_bytes, decrypt_text
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.customer import Customer
from app.models.billing.document_series import DocumentSeries
from app.models.billing.enums import (
    MH_IDENTIFICATION_CODES,
    DocumentSeriesType,
    HaciendaDocumentType,
    HaciendaEnvironment,
    HaciendaFiscalStatus,
    IdentificationType,
    InvoiceStatus,
    tax_rate_to_mh_code,
)
from app.models.billing.fiscal_profile import OrganizationFiscalProfile
from app.models.billing.hacienda_credential import OrganizationHaciendaCredential
from app.models.billing.invoice import Invoice, InvoiceLine
from app.models.billing.invoice_fiscal import InvoiceFiscal
from app.schemas.responses.billing import InvoiceFiscalResponse
from app.services.audit_service import AuditService
from app.services.billing.hacienda import (
    HaciendaClient,
    build_clave,
    build_consecutive,
    build_factura_electronica_xml,
    sign_factura_xml,
)
from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
)


class HaciendaEmitService:
    @staticmethod
    def _fiscal_response(row: InvoiceFiscal) -> InvoiceFiscalResponse:
        return InvoiceFiscalResponse.model_validate(row)

    @staticmethod
    async def get_for_invoice(
        session: AsyncSession,
        invoice_id: UUID,
    ) -> Optional[InvoiceFiscalResponse]:
        Fiscal = cast(Any, InvoiceFiscal)
        row = (
            await session.execute(
                select(InvoiceFiscal).where(Fiscal.invoice_id == invoice_id)
            )
        ).scalar_one_or_none()
        return HaciendaEmitService._fiscal_response(row) if row else None

    @staticmethod
    async def _allocate_fe_sequence(session: AsyncSession, org_id: UUID) -> int:
        SeriesModel = cast(Any, DocumentSeries)
        stmt = (
            select(DocumentSeries)
            .where(
                SeriesModel.organization_id == org_id,
                SeriesModel.doc_type == DocumentSeriesType.FE.value,
            )
            .with_for_update()
        )
        series = (await session.execute(stmt)).scalar_one_or_none()
        if not series:
            series = DocumentSeries(
                organization_id=org_id,
                doc_type=DocumentSeriesType.FE.value,
                prefix="FE-",
                next_number=1,
                padding=10,
            )
            session.add(series)
            await session.flush()
        number = series.next_number
        series.next_number = number + 1
        return number

    @staticmethod
    def _id_type_code(value: str | None) -> str:
        if not value:
            return MH_IDENTIFICATION_CODES[IdentificationType.JURIDICA]
        try:
            return MH_IDENTIFICATION_CODES[IdentificationType(value)]
        except ValueError:
            return MH_IDENTIFICATION_CODES[IdentificationType.JURIDICA]

    @staticmethod
    async def emit(
        session: AsyncSession,
        org_id: UUID,
        invoice_id: UUID,
    ) -> InvoiceFiscalResponse:
        InvoiceModel = cast(Any, Invoice)
        invoice = (
            await session.execute(select(Invoice).where(InvoiceModel.id == invoice_id))
        ).scalar_one_or_none()
        if not invoice or invoice.organization_id != org_id:
            raise EntityNotFoundError(entity="invoice")
        if invoice.status == InvoiceStatus.DRAFT.value:
            raise NidusException(
                code="INVOICE_NOT_ISSUED",
                message_key="billing.invoice_must_be_issued",
                status_code=400,
            )
        if invoice.status == InvoiceStatus.VOID.value:
            raise NidusException(
                code="INVOICE_VOID",
                message_key="billing.invoice_void",
                status_code=400,
            )

        Fiscal = cast(Any, InvoiceFiscal)
        existing = (
            await session.execute(
                select(InvoiceFiscal).where(Fiscal.invoice_id == invoice_id)
            )
        ).scalar_one_or_none()
        if existing and existing.status in {
            HaciendaFiscalStatus.ACCEPTED.value,
            HaciendaFiscalStatus.SUBMITTED.value,
            HaciendaFiscalStatus.PROCESSING.value,
        }:
            raise NidusException(
                code="INVOICE_ALREADY_EMITTED",
                message_key="billing.invoice_already_emitted",
                status_code=409,
            )

        Profile = cast(Any, OrganizationFiscalProfile)
        profile = (
            await session.execute(
                select(OrganizationFiscalProfile).where(Profile.organization_id == org_id)
            )
        ).scalar_one_or_none()
        if not profile:
            raise NidusException(
                code="FISCAL_PROFILE_REQUIRED",
                message_key="billing.fiscal_profile_required",
                status_code=400,
            )

        CustomerModel = cast(Any, Customer)
        customer = (
            await session.execute(
                select(Customer).where(CustomerModel.id == invoice.customer_id)
            )
        ).scalar_one_or_none()
        if not customer:
            raise EntityNotFoundError(entity="customer")
        if not customer.tax_id:
            raise NidusException(
                code="CUSTOMER_TAX_ID_REQUIRED",
                message_key="billing.customer_tax_id_required",
                status_code=400,
            )

        LineModel = cast(Any, InvoiceLine)
        lines = (
            await session.execute(
                select(InvoiceLine)
                .where(LineModel.invoice_id == invoice_id)
                .order_by(LineModel.line_number)
            )
        ).scalars().all()
        if not lines:
            raise NidusException(
                code="INVOICE_LINES_REQUIRED",
                message_key="billing.invoice_lines_required",
                status_code=400,
            )

        Cred = cast(Any, OrganizationHaciendaCredential)
        credential = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(Cred.organization_id == org_id)
            )
        ).scalar_one_or_none()

        issued_at = invoice.issued_at or datetime.now(timezone.utc)
        if issued_at.tzinfo is None:
            issued_at = issued_at.replace(tzinfo=timezone.utc)

        sequence = await HaciendaEmitService._allocate_fe_sequence(session, org_id)
        consecutive = build_consecutive(
            branch_code=profile.branch_code or "001",
            document_type=HaciendaDocumentType.FE.value,
            sequence=sequence,
        )
        clave = build_clave(
            issued_at=issued_at,
            emitter_id=profile.identification_number,
            consecutive=consecutive,
        )

        xml_lines: list[XmlLine] = []
        for line in lines:
            rate = Decimal(line.tax_rate) if line.tax_rate is not None else None
            code = line.tax_code or tax_rate_to_mh_code(
                float(rate) if rate is not None else None
            )
            xml_lines.append(
                XmlLine(
                    number=line.line_number,
                    description=line.description,
                    quantity=Decimal(line.quantity),
                    unit=line.unit,
                    unit_price=Decimal(line.unit_price),
                    subtotal=Decimal(line.line_subtotal),
                    tax_amount=Decimal(line.line_tax),
                    total=Decimal(line.line_total),
                    tax_rate=rate,
                    tax_code=code,
                    cabys_code=line.cabys_code,
                    sku=line.sku,
                )
            )

        xml_input = FacturaElectronicaInput(
            clave=clave,
            consecutive=consecutive,
            issued_at=issued_at,
            currency=invoice.currency,
            emitter=XmlParty(
                identification_type_code=HaciendaEmitService._id_type_code(
                    profile.identification_type
                ),
                identification_number="".join(
                    ch for ch in profile.identification_number if ch.isdigit()
                ),
                name=profile.legal_name,
                province=profile.province,
                canton=profile.canton,
                district=profile.district,
                other_signs=profile.other_signs,
                phone=profile.phone,
                email=profile.email,
                economic_activity_code=profile.economic_activity_code,
            ),
            receptor=XmlParty(
                identification_type_code=HaciendaEmitService._id_type_code(
                    customer.identification_type
                ),
                identification_number="".join(
                    ch for ch in customer.tax_id if ch.isdigit()
                ),
                name=customer.name,
                email=customer.email,
            ),
            lines=xml_lines,
            subtotal=Decimal(invoice.subtotal),
            tax_total=Decimal(invoice.tax_total),
            total=Decimal(invoice.total),
            payment_condition=invoice.payment_condition,
        )
        xml_unsigned = build_factura_electronica_xml(xml_input)

        p12_bytes = None
        p12_password = None
        api_password = None
        if credential and credential.p12_ciphertext and credential.p12_password_ciphertext:
            p12_bytes = decrypt_bytes(credential.p12_ciphertext)
            p12_password = decrypt_text(credential.p12_password_ciphertext)
        if credential and credential.pin_ciphertext:
            api_password = decrypt_text(credential.pin_ciphertext)

        try:
            sign_result = sign_factura_xml(
                xml_unsigned,
                p12_bytes=p12_bytes,
                p12_password=p12_password,
            )
        except NotImplementedError:
            sign_result = sign_factura_xml(
                xml_unsigned,
                p12_bytes=None,
                p12_password=None,
            )

        live = bool(settings.HACIENDA_LIVE) and not sign_result.mock
        client = HaciendaClient(
            environment=HaciendaEnvironment(
                credential.environment
                if credential
                else HaciendaEnvironment.SANDBOX.value
            ),
            username=(credential.username if credential and credential.username else ""),
            password=api_password or "",
            client_id=(
                credential.oauth_client_id if credential and credential.oauth_client_id else ""
            ),
            client_secret=(
                decrypt_text(credential.oauth_client_secret_ciphertext)
                if credential and credential.oauth_client_secret_ciphertext
                else ""
            ),
            live=live and bool(credential and credential.username and api_password),
        )

        submit = await client.submit(
            clave=clave,
            issued_at=issued_at,
            emitter_type=xml_input.emitter.identification_type_code,
            emitter_number=xml_input.emitter.identification_number,
            receptor_type=xml_input.receptor.identification_type_code,
            receptor_number=xml_input.receptor.identification_number,
            xml_signed=sign_result.xml_signed,
        )

        now = datetime.now(timezone.utc)
        row = existing or InvoiceFiscal(
            organization_id=org_id,
            invoice_id=invoice_id,
            document_type=HaciendaDocumentType.FE.value,
        )
        if existing is None:
            session.add(row)

        row.clave = clave
        row.consecutive = consecutive
        row.security_code = clave[-8:]
        row.xml_unsigned = xml_unsigned
        row.xml_signed = sign_result.xml_signed
        row.signed_at = now
        row.submitted_at = now
        row.status = submit.status.value
        row.mh_status_raw = submit.raw_status
        row.mh_message = submit.message
        row.mh_response_xml = submit.response_xml
        row.mock_mode = submit.mock or sign_result.mock
        row.document_type = HaciendaDocumentType.FE.value
        row.supply_situation = "1"

        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_FISCAL_EMIT,
            organization_id=org_id,
            resource_type=AuditResourceType.INVOICE_FISCAL,
            resource_id=row.id,
            details={
                "invoice_id": str(invoice_id),
                "clave": clave,
                "status": row.status,
                "mock_mode": row.mock_mode,
            },
        )
        await session.refresh(row)
        response = HaciendaEmitService._fiscal_response(row)
        await session.commit()
        return response

    @staticmethod
    async def verify(
        session: AsyncSession,
        org_id: UUID,
        invoice_id: UUID,
    ) -> InvoiceFiscalResponse:
        Fiscal = cast(Any, InvoiceFiscal)
        row = (
            await session.execute(
                select(InvoiceFiscal).where(Fiscal.invoice_id == invoice_id)
            )
        ).scalar_one_or_none()
        if not row or row.organization_id != org_id:
            raise EntityNotFoundError(entity="invoice_fiscal")
        if not row.clave:
            raise NidusException(
                code="CLAVE_REQUIRED",
                message_key="billing.fiscal_clave_required",
                status_code=400,
            )

        Cred = cast(Any, OrganizationHaciendaCredential)
        credential = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(Cred.organization_id == org_id)
            )
        ).scalar_one_or_none()

        live = bool(settings.HACIENDA_LIVE) and not row.mock_mode
        api_password = ""
        client_secret = ""
        if credential and credential.pin_ciphertext:
            api_password = decrypt_text(credential.pin_ciphertext)
        if credential and credential.oauth_client_secret_ciphertext:
            client_secret = decrypt_text(credential.oauth_client_secret_ciphertext)

        client = HaciendaClient(
            environment=HaciendaEnvironment(
                credential.environment
                if credential
                else HaciendaEnvironment.SANDBOX.value
            ),
            username=(credential.username if credential and credential.username else ""),
            password=api_password,
            client_id=(
                credential.oauth_client_id if credential and credential.oauth_client_id else ""
            ),
            client_secret=client_secret,
            live=live and bool(credential and credential.username and api_password),
        )
        result = await client.verify(row.clave)
        row.status = result.status.value
        row.mh_status_raw = result.raw_status
        row.mh_message = result.message
        row.mh_response_xml = result.response_xml
        row.mh_response_at = datetime.now(timezone.utc)
        row.mock_mode = row.mock_mode or result.mock

        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INVOICE_FISCAL_VERIFY,
            organization_id=org_id,
            resource_type=AuditResourceType.INVOICE_FISCAL,
            resource_id=row.id,
            details={
                "invoice_id": str(invoice_id),
                "clave": row.clave,
                "status": row.status,
                "mock_mode": row.mock_mode,
            },
        )
        await session.refresh(row)
        response = HaciendaEmitService._fiscal_response(row)
        await session.commit()
        return response
