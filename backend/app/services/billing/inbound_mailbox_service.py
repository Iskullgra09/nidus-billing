from __future__ import annotations

import base64
import re
import secrets
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.base import NidusException
from app.core.rls import clear_rls_context, set_rls_context
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.enums import InboundIngestChannel
from app.models.billing.inbound_mailbox import OrganizationInboundMailbox
from app.models.organization.organization import Organization
from app.schemas.requests.billing import (
    InboundDocumentCreate,
    InboundMailboxUpdate,
    InboundMailboxWebhookPayload,
)
from app.schemas.responses.billing import InboundDocumentResponse, InboundMailboxResponse
from app.services.audit_service import AuditService
from app.services.billing.hacienda_inbound_service import HaciendaInboundService

_LOCAL_PART_RE = re.compile(r"[^a-z0-9-]+")
_EMAIL_LOCAL_RE = re.compile(r"^([^@\s]+)@")


def _sanitize_local_part(slug: str, suffix: str) -> str:
    base = _LOCAL_PART_RE.sub("-", slug.lower()).strip("-") or "org"
    base = base[:40].rstrip("-")
    return f"{base}-{suffix}"


def _extract_local_part(to_address: str) -> str:
    match = _EMAIL_LOCAL_RE.match(to_address.strip().lower())
    if not match:
        raise NidusException(
            code="INBOUND_MAILBOX_ADDRESS_INVALID",
            message_key="billing.inbound_mailbox_address_invalid",
            status_code=400,
        )
    return match.group(1)


def _decode_attachment_xml(
    *,
    filename: str | None,
    content: str | None,
    content_base64: str | None,
) -> str | None:
    raw: str | None = None
    if content and content.strip():
        raw = content.strip()
    elif content_base64 and content_base64.strip():
        try:
            decoded = base64.b64decode(content_base64, validate=False)
            raw = decoded.decode("utf-8", errors="replace").strip()
        except Exception:
            return None
    if not raw:
        return None
    name = (filename or "").lower()
    looks_xml = name.endswith(".xml") or "<FacturaElectronica" in raw or "FacturaElectronica" in raw
    if not looks_xml:
        return None
    return raw


class InboundMailboxService:
    @staticmethod
    def _to_response(row: OrganizationInboundMailbox) -> InboundMailboxResponse:
        domain = settings.INBOUND_MAILBOX_DOMAIN.strip().lower()
        return InboundMailboxResponse(
            organization_id=row.organization_id,
            local_part=row.local_part,
            domain=domain,
            address=f"{row.local_part}@{domain}",
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    async def _ensure_row(
        session: AsyncSession,
        org_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None,
    ) -> tuple[OrganizationInboundMailbox, bool]:
        Model = cast(Any, OrganizationInboundMailbox)
        row = (
            await session.execute(
                select(OrganizationInboundMailbox).where(Model.organization_id == org_id)
            )
        ).scalar_one_or_none()
        if row:
            return row, False

        OrgModel = cast(Any, Organization)
        org = (
            await session.execute(
                select(Organization).where(
                    OrgModel.id == org_id,
                    OrgModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if not org:
            raise NidusException(
                code="ORGANIZATION_NOT_FOUND",
                message_key="common.not_found",
                status_code=404,
            )

        suffix = secrets.token_hex(3)
        local_part = _sanitize_local_part(org.slug, suffix)
        row = OrganizationInboundMailbox(
            organization_id=org_id,
            local_part=local_part,
            enabled=True,
        )
        session.add(row)
        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INBOUND_MAILBOX_UPSERT,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_MAILBOX,
            resource_id=row.id,
            details={"local_part": row.local_part, "enabled": True, "provisioned": True},
            ip_address=ip_address,
        )
        await session.refresh(row)
        return row, True

    @staticmethod
    async def get_or_provision(
        session: AsyncSession,
        org_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None,
    ) -> InboundMailboxResponse:
        row, provisioned = await InboundMailboxService._ensure_row(
            session,
            org_id,
            actor_user_id=actor_user_id,
            ip_address=ip_address,
        )
        if provisioned:
            await session.commit()
        return InboundMailboxService._to_response(row)

    @staticmethod
    async def update(
        session: AsyncSession,
        org_id: UUID,
        data: InboundMailboxUpdate,
        *,
        actor_user_id: UUID,
        ip_address: str | None,
    ) -> InboundMailboxResponse:
        row, _ = await InboundMailboxService._ensure_row(
            session,
            org_id,
            actor_user_id=actor_user_id,
            ip_address=ip_address,
        )
        row.enabled = data.enabled
        session.add(row)
        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.INBOUND_MAILBOX_UPSERT,
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type=AuditResourceType.INBOUND_MAILBOX,
            resource_id=row.id,
            details={"local_part": row.local_part, "enabled": row.enabled},
            ip_address=ip_address,
        )
        await session.refresh(row)
        await session.commit()
        return InboundMailboxService._to_response(row)

    @staticmethod
    def verify_webhook_secret(provided: str | None) -> None:
        expected = settings.INBOUND_MAILBOX_WEBHOOK_SECRET or ""
        if not expected:
            raise NidusException(
                code="INBOUND_MAILBOX_WEBHOOK_DISABLED",
                message_key="billing.inbound_mailbox_webhook_disabled",
                status_code=503,
            )
        if not provided or not secrets.compare_digest(provided, expected):
            raise NidusException(
                code="INBOUND_MAILBOX_WEBHOOK_UNAUTHORIZED",
                message_key="billing.inbound_mailbox_webhook_unauthorized",
                status_code=401,
            )

    @staticmethod
    async def ingest_webhook(
        session: AsyncSession,
        payload: InboundMailboxWebhookPayload,
        *,
        ip_address: str | None,
    ) -> InboundDocumentResponse:
        local_part = _extract_local_part(payload.to)
        await clear_rls_context(session)
        MailboxModel = cast(Any, OrganizationInboundMailbox)
        mailbox = (
            await session.execute(
                select(OrganizationInboundMailbox).where(
                    MailboxModel.local_part == local_part,
                )
            )
        ).scalar_one_or_none()
        if not mailbox:
            raise NidusException(
                code="INBOUND_MAILBOX_NOT_FOUND",
                message_key="billing.inbound_mailbox_not_found",
                status_code=404,
            )
        if not mailbox.enabled:
            raise NidusException(
                code="INBOUND_MAILBOX_DISABLED",
                message_key="billing.inbound_mailbox_disabled",
                status_code=400,
            )

        xml: str | None = None
        for attachment in payload.attachments:
            xml = _decode_attachment_xml(
                filename=attachment.filename,
                content=attachment.content,
                content_base64=attachment.content_base64,
            )
            if xml:
                break
        if not xml:
            raise NidusException(
                code="INBOUND_MAILBOX_XML_REQUIRED",
                message_key="billing.inbound_mailbox_xml_required",
                status_code=400,
            )

        note_bits = ["Imported from email"]
        if payload.from_address:
            note_bits.append(f"from={payload.from_address}")
        if payload.subject:
            note_bits.append(f"subject={payload.subject[:120]}")
        notes = "; ".join(note_bits)

        await set_rls_context(session, mailbox.organization_id, None)
        return await HaciendaInboundService.create_from_xml(
            session,
            mailbox.organization_id,
            InboundDocumentCreate(xml=xml, notes=notes),
            actor_user_id=None,
            ip_address=ip_address,
            ingest_channel=InboundIngestChannel.EMAIL,
            on_clave_exists="return_existing",
        )
