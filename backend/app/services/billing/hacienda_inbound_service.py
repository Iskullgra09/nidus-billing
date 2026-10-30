from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.base import EntityNotFoundError, NidusException
from app.core.field_encryption import decrypt_bytes, decrypt_text
from app.core.pagination import paginate_with_cursor
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.document_series import DocumentSeries
from app.models.billing.enums import (
    MH_IDENTIFICATION_CODES,
    DocumentSeriesType,
    HaciendaEnvironment,
    HaciendaFiscalStatus,
    IdentificationType,
    InboundIngestChannel,
    MensajeReceptorCode,
)
from app.models.billing.fiscal_profile import OrganizationFiscalProfile
from app.models.billing.hacienda_credential import OrganizationHaciendaCredential
from app.models.billing.inbound_document import InboundFiscalDocument
from app.models.billing.supplier import Supplier
from app.schemas.filters.billing import InboundFilter
from app.schemas.requests.billing import InboundDocumentCreate, InboundDocumentLink
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.billing import InboundDocumentResponse
from app.schemas.responses.pagination import CursorPage, PageInfo
from app.services.audit_service import AuditService
from app.services.billing.hacienda import (
    HaciendaClient,
    build_consecutive,
    build_mensaje_receptor_xml,
    humanize_mh_message,
    parse_inbound_factura_xml,
    sign_factura_xml,
)
from app.services.billing.hacienda.xml_mensaje import MensajeReceptorInput


def _humanize_inbound_mh_message(
    mh_message: str | None,
    mh_response_xml: str | None,
) -> str | None:
    return humanize_mh_message(mh_message) or humanize_mh_message(mh_response_xml)


class HaciendaInboundService:
    @staticmethod
    def _digits(value: str | None) -> str:
        return "".join(ch for ch in (value or "") if ch.isdigit())

    @staticmethod
    def _to_response(
        row: InboundFiscalDocument,
        supplier_name: str | None = None,
    ) -> InboundDocumentResponse:
        return InboundDocumentResponse(
            id=row.id,
            organization_id=row.organization_id,
            supplier_id=row.supplier_id,
            supplier_name=supplier_name,
            clave=row.clave,
            consecutive=row.consecutive,
            document_type=row.document_type,
            status=row.status,
            ingest_channel=row.ingest_channel,
            emitter_identification_type=row.emitter_identification_type,
            emitter_identification_number=row.emitter_identification_number,
            emitter_name=row.emitter_name,
            emitter_email=row.emitter_email,
            issued_at=row.issued_at,
            currency=row.currency,
            exchange_rate=row.exchange_rate,
            subtotal=row.subtotal,
            tax_total=row.tax_total,
            total=row.total,
            mensaje_tipo=row.mensaje_tipo,
            mensaje_detalle=row.mensaje_detalle,
            mensaje_submitted_at=row.mensaje_submitted_at,
            mh_response_at=row.mh_response_at,
            mh_status_raw=row.mh_status_raw,
            mh_message=_humanize_inbound_mh_message(row.mh_message, row.mh_response_xml),
            mock_mode=row.mock_mode,
            notes=row.notes,
            received_at=row.received_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    async def _get_row(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
    ) -> InboundFiscalDocument:
        Model = cast(Any, InboundFiscalDocument)
        row = (
            await session.execute(
                select(InboundFiscalDocument).where(
                    Model.id == document_id,
                    Model.organization_id == org_id,
                    Model.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity="inbound")
        return row

    @staticmethod
    async def _supplier_name(session: AsyncSession, supplier_id: UUID | None) -> str | None:
        if not supplier_id:
            return None
        SupplierModel = cast(Any, Supplier)
        name = (
            await session.execute(
                select(SupplierModel.name).where(SupplierModel.id == supplier_id)
            )
        ).scalar_one_or_none()
        return name

    @staticmethod
    async def _match_supplier(
        session: AsyncSession,
        org_id: UUID,
        emitter_number: str | None,
    ) -> UUID | None:
        digits = HaciendaInboundService._digits(emitter_number)
        if not digits:
            return None
        SupplierModel = cast(Any, Supplier)
        rows = (
            await session.execute(
                select(Supplier).where(
                    SupplierModel.organization_id == org_id,
                    SupplierModel.deleted_at.is_(None),
                    SupplierModel.tax_id.is_not(None),
                )
            )
        ).scalars().all()
        for supplier in rows:
            if HaciendaInboundService._digits(supplier.tax_id) == digits:
                return supplier.id
        return None

    @staticmethod
    async def _allocate_mensaje_sequence(session: AsyncSession, org_id: UUID) -> int:
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
        current = int(series.next_number)
        series.next_number = current + 1
        await session.flush()
        return current

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        pagination: CursorParams,
        filters: InboundFilter,
    ) -> CursorPage[InboundDocumentResponse]:
        Model = cast(Any, InboundFiscalDocument)
        stmt = select(InboundFiscalDocument).where(Model.deleted_at.is_(None))
        if filters.q:
            term = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(
                    Model.clave.ilike(term),
                    Model.emitter_name.ilike(term),
                    Model.emitter_identification_number.ilike(term),
                )
            )
        if filters.status:
            stmt = stmt.where(Model.status == filters.status)
        if filters.supplier_id:
            stmt = stmt.where(Model.supplier_id == UUID(filters.supplier_id))

        rows, end_cursor, has_next = await paginate_with_cursor(
            session=session,
            stmt=stmt,
            model_class=Model,
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
        supplier_ids = {row.supplier_id for row in rows if row.supplier_id}
        names: dict[UUID, str] = {}
        if supplier_ids:
            SupplierModel = cast(Any, Supplier)
            name_rows = (
                await session.execute(
                    select(SupplierModel.id, SupplierModel.name).where(
                        SupplierModel.id.in_(supplier_ids)
                    )
                )
            ).all()
            names = {row[0]: row[1] for row in name_rows}
        items = [
            HaciendaInboundService._to_response(row, names.get(row.supplier_id) if row.supplier_id else None)
            for row in rows
        ]
        return CursorPage(
            items=items,
            page_info=PageInfo(has_next_page=has_next, end_cursor=end_cursor),
        )

    @staticmethod
    async def get_document(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
    ) -> InboundDocumentResponse:
        row = await HaciendaInboundService._get_row(session, org_id, document_id)
        name = await HaciendaInboundService._supplier_name(session, row.supplier_id)
        return HaciendaInboundService._to_response(row, name)

    @staticmethod
    async def create_from_xml(
        session: AsyncSession,
        org_id: UUID,
        data: InboundDocumentCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None,
        ingest_channel: InboundIngestChannel = InboundIngestChannel.MANUAL_UPLOAD,
        on_clave_exists: str = "error",
    ) -> InboundDocumentResponse:
        try:
            parsed = parse_inbound_factura_xml(data.xml)
        except Exception as exc:
            raise NidusException(
                code="INBOUND_XML_INVALID",
                message_key="billing.inbound_xml_invalid",
                status_code=400,
                error=str(exc)[:200],
            ) from exc

        Model = cast(Any, InboundFiscalDocument)
        existing = (
            await session.execute(
                select(InboundFiscalDocument).where(
                    Model.organization_id == org_id,
                    Model.clave == parsed.clave,
                    Model.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            if on_clave_exists == "return_existing":
                name = await HaciendaInboundService._supplier_name(session, existing.supplier_id)
                return HaciendaInboundService._to_response(existing, name)
            raise NidusException(
                code="INBOUND_CLAVE_EXISTS",
                message_key="billing.inbound_clave_exists",
                status_code=409,
            )

        supplier_id = data.supplier_id
        if supplier_id is None:
            supplier_id = await HaciendaInboundService._match_supplier(
                session, org_id, parsed.emitter_identification_number
            )
        elif supplier_id is not None:
            SupplierModel = cast(Any, Supplier)
            supplier = (
                await session.execute(
                    select(Supplier).where(
                        SupplierModel.id == supplier_id,
                        SupplierModel.organization_id == org_id,
                        SupplierModel.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if not supplier:
                raise EntityNotFoundError(entity="supplier")

        row = InboundFiscalDocument(
            organization_id=org_id,
            supplier_id=supplier_id,
            clave=parsed.clave,
            consecutive=parsed.consecutive,
            document_type=parsed.document_type,
            status=HaciendaFiscalStatus.PENDING.value,
            ingest_channel=ingest_channel.value,
            emitter_identification_type=parsed.emitter_identification_type,
            emitter_identification_number=parsed.emitter_identification_number,
            emitter_name=parsed.emitter_name,
            emitter_email=parsed.emitter_email,
            issued_at=parsed.issued_at,
            currency=parsed.currency,
            exchange_rate=parsed.exchange_rate,
            subtotal=parsed.subtotal,
            tax_total=parsed.tax_total,
            total=parsed.total,
            xml_received=data.xml,
            notes=data.notes,
            received_at=date.today(),
            mock_mode=True,
        )
        session.add(row)
        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INBOUND_CREATE,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_FISCAL,
            resource_id=row.id,
            details={"clave": row.clave, "ingest_channel": ingest_channel.value},
            ip_address=ip_address,
        )
        await session.refresh(row)
        name = await HaciendaInboundService._supplier_name(session, row.supplier_id)
        response = HaciendaInboundService._to_response(row, name)
        await session.commit()
        return response

    @staticmethod
    async def link_supplier(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
        data: InboundDocumentLink,
        *,
        actor_user_id: UUID,
        ip_address: str | None,
    ) -> InboundDocumentResponse:
        row = await HaciendaInboundService._get_row(session, org_id, document_id)
        if data.supplier_id is not None:
            SupplierModel = cast(Any, Supplier)
            supplier = (
                await session.execute(
                    select(Supplier).where(
                        SupplierModel.id == data.supplier_id,
                        SupplierModel.organization_id == org_id,
                        SupplierModel.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if not supplier:
                raise EntityNotFoundError(entity="supplier")
        row.supplier_id = data.supplier_id
        if data.notes is not None:
            row.notes = data.notes
        await AuditService.record(
            session,
            action=AuditAction.INBOUND_LINK,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_FISCAL,
            resource_id=row.id,
            details={"supplier_id": str(data.supplier_id) if data.supplier_id else None},
            ip_address=ip_address,
        )
        await session.refresh(row)
        name = await HaciendaInboundService._supplier_name(session, row.supplier_id)
        response = HaciendaInboundService._to_response(row, name)
        await session.commit()
        return response

    @staticmethod
    async def _submit_mensaje(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
        *,
        mensaje: MensajeReceptorCode,
        detalle: str | None,
        actor_user_id: UUID,
        ip_address: str | None,
        audit_action: AuditAction,
    ) -> InboundDocumentResponse:
        row = await HaciendaInboundService._get_row(session, org_id, document_id)
        if row.status in {
            HaciendaFiscalStatus.SUBMITTED.value,
            HaciendaFiscalStatus.PROCESSING.value,
            HaciendaFiscalStatus.ACCEPTED.value,
        }:
            raise NidusException(
                code="INBOUND_ALREADY_ANSWERED",
                message_key="billing.inbound_already_answered",
                status_code=409,
            )
        if mensaje == MensajeReceptorCode.REJECTED and not (detalle and detalle.strip()):
            raise NidusException(
                code="INBOUND_REJECT_REASON_REQUIRED",
                message_key="billing.inbound_reject_reason_required",
                status_code=400,
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

        Cred = cast(Any, OrganizationHaciendaCredential)
        credential = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(Cred.organization_id == org_id)
            )
        ).scalar_one_or_none()

        p12_bytes = None
        p12_password = None
        api_password = None
        if credential and credential.p12_ciphertext and credential.p12_password_ciphertext:
            p12_bytes = decrypt_bytes(credential.p12_ciphertext)
            p12_password = decrypt_text(credential.p12_password_ciphertext)
        if credential and credential.pin_ciphertext:
            api_password = decrypt_text(credential.pin_ciphertext)

        live = bool(settings.HACIENDA_LIVE)
        if live and (not p12_bytes or p12_password is None):
            raise NidusException(
                code="HACIENDA_P12_REQUIRED",
                message_key="billing.hacienda_p12_required",
                status_code=400,
            )

        sequence = await HaciendaInboundService._allocate_mensaje_sequence(session, org_id)
        consecutive = build_consecutive(
            branch_code=profile.branch_code or "001",
            document_type="05",
            sequence=sequence,
        )
        issued_at = row.issued_at or datetime.now(timezone.utc)
        if issued_at.tzinfo is None:
            issued_at = issued_at.replace(tzinfo=timezone.utc)

        emitter_number = HaciendaInboundService._digits(row.emitter_identification_number)
        receptor_number = HaciendaInboundService._digits(profile.identification_number)
        xml_unsigned = build_mensaje_receptor_xml(
            MensajeReceptorInput(
                clave=row.clave,
                emitter_number=emitter_number,
                receptor_number=receptor_number,
                consecutive_receptor=consecutive,
                issued_at=issued_at,
                mensaje=mensaje,
                detalle=detalle,
                tax_total=Decimal(row.tax_total),
                total=Decimal(row.total),
            )
        )

        try:
            sign_result = sign_factura_xml(
                xml_unsigned,
                p12_bytes=p12_bytes,
                p12_password=p12_password,
            )
        except Exception as exc:
            if live:
                raise NidusException(
                    code="HACIENDA_SIGN_FAILED",
                    message_key="billing.hacienda_sign_failed",
                    status_code=400,
                    error=str(exc)[:300],
                ) from exc
            sign_result = sign_factura_xml(
                xml_unsigned,
                p12_bytes=None,
                p12_password=None,
            )

        if live and sign_result.mock:
            raise NidusException(
                code="HACIENDA_SIGN_REQUIRED",
                message_key="billing.hacienda_sign_required",
                status_code=400,
            )

        client = HaciendaClient(
            environment=HaciendaEnvironment(
                credential.environment if credential else HaciendaEnvironment.SANDBOX.value
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
            live=live
            and not sign_result.mock
            and bool(credential and credential.username and api_password),
        )

        id_type = IdentificationType(profile.identification_type)
        submit = await client.submit_mensaje_receptor(
            clave=row.clave,
            issued_at=datetime.now(timezone.utc),
            emitter_type=row.emitter_identification_type
            or MH_IDENTIFICATION_CODES[IdentificationType.JURIDICA],
            emitter_number=emitter_number,
            receptor_type=MH_IDENTIFICATION_CODES[id_type],
            receptor_number=receptor_number,
            xml_signed=sign_result.xml_signed,
        )

        now = datetime.now(timezone.utc)
        row.mensaje_tipo = mensaje.value
        row.mensaje_detalle = detalle
        row.mensaje_xml_signed = sign_result.xml_signed
        row.mensaje_submitted_at = now
        row.status = submit.status.value
        row.mh_status_raw = submit.raw_status
        row.mh_message = submit.message
        row.mh_response_xml = submit.response_xml
        row.mock_mode = submit.mock or sign_result.mock

        await AuditService.record(
            session,
            action=audit_action,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_FISCAL,
            resource_id=row.id,
            details={"clave": row.clave, "mensaje": mensaje.value},
            ip_address=ip_address,
        )
        await session.refresh(row)
        name = await HaciendaInboundService._supplier_name(session, row.supplier_id)
        response = HaciendaInboundService._to_response(row, name)
        await session.commit()
        return response

    @staticmethod
    async def accept(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
        *,
        actor_user_id: UUID,
        ip_address: str | None,
    ) -> InboundDocumentResponse:
        return await HaciendaInboundService._submit_mensaje(
            session,
            org_id,
            document_id,
            mensaje=MensajeReceptorCode.ACCEPTED,
            detalle="Aceptado",
            actor_user_id=actor_user_id,
            ip_address=ip_address,
            audit_action=AuditAction.INBOUND_ACCEPT,
        )

    @staticmethod
    async def reject(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
        *,
        reason: str,
        actor_user_id: UUID,
        ip_address: str | None,
    ) -> InboundDocumentResponse:
        return await HaciendaInboundService._submit_mensaje(
            session,
            org_id,
            document_id,
            mensaje=MensajeReceptorCode.REJECTED,
            detalle=reason.strip(),
            actor_user_id=actor_user_id,
            ip_address=ip_address,
            audit_action=AuditAction.INBOUND_REJECT,
        )

    @staticmethod
    async def verify(
        session: AsyncSession,
        org_id: UUID,
        document_id: UUID,
        *,
        actor_user_id: UUID,
        ip_address: str | None,
    ) -> InboundDocumentResponse:
        row = await HaciendaInboundService._get_row(session, org_id, document_id)
        if not row.mensaje_submitted_at:
            raise NidusException(
                code="INBOUND_NOT_SUBMITTED",
                message_key="billing.inbound_not_submitted",
                status_code=400,
            )

        Cred = cast(Any, OrganizationHaciendaCredential)
        credential = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(Cred.organization_id == org_id)
            )
        ).scalar_one_or_none()
        api_password = None
        if credential and credential.pin_ciphertext:
            api_password = decrypt_text(credential.pin_ciphertext)

        live = bool(settings.HACIENDA_LIVE) and not row.mock_mode
        client = HaciendaClient(
            environment=HaciendaEnvironment(
                credential.environment if credential else HaciendaEnvironment.SANDBOX.value
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
        result = await client.verify(row.clave)
        row.status = result.status.value
        row.mh_status_raw = result.raw_status
        row.mh_message = result.message
        row.mh_response_xml = result.response_xml
        row.mh_response_at = datetime.now(timezone.utc)
        row.mock_mode = result.mock or row.mock_mode

        await AuditService.record(
            session,
            action=AuditAction.INBOUND_VERIFY,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_FISCAL,
            resource_id=row.id,
            details={"clave": row.clave, "status": row.status},
            ip_address=ip_address,
        )
        await session.refresh(row)
        name = await HaciendaInboundService._supplier_name(session, row.supplier_id)
        response = HaciendaInboundService._to_response(row, name)
        await session.commit()
        return response
