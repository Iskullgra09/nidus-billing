from typing import Any, Optional, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.field_encryption import encrypt_bytes, encrypt_text
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.enums import HaciendaEnvironment
from app.models.billing.fiscal_profile import OrganizationFiscalProfile
from app.models.billing.hacienda_credential import OrganizationHaciendaCredential
from app.schemas.requests.billing import FiscalProfileUpsert, HaciendaCredentialUpsert
from app.schemas.responses.billing import (
    FiscalProfileResponse,
    HaciendaCredentialStatusResponse,
)
from app.services.audit_service import AuditService


class FiscalService:
    @staticmethod
    def _profile_response(row: OrganizationFiscalProfile) -> FiscalProfileResponse:
        return FiscalProfileResponse.model_validate(row)

    @staticmethod
    def _credential_status(
        row: Optional[OrganizationHaciendaCredential],
    ) -> HaciendaCredentialStatusResponse:
        if not row:
            return HaciendaCredentialStatusResponse(
                configured=False,
                environment=HaciendaEnvironment.SANDBOX.value,
                username=None,
                has_p12=False,
                has_p12_password=False,
                has_pin=False,
                has_oauth_client_secret=False,
                oauth_client_id=None,
                updated_at=None,
            )
        return HaciendaCredentialStatusResponse(
            configured=bool(row.p12_ciphertext or row.username or row.oauth_client_id),
            environment=row.environment,
            username=row.username,
            has_p12=row.p12_ciphertext is not None,
            has_p12_password=row.p12_password_ciphertext is not None,
            has_pin=row.pin_ciphertext is not None,
            has_oauth_client_secret=row.oauth_client_secret_ciphertext is not None,
            oauth_client_id=row.oauth_client_id,
            updated_at=row.updated_at,
        )

    @staticmethod
    async def get_profile(
        session: AsyncSession,
        organization_id: UUID,
    ) -> Optional[FiscalProfileResponse]:
        Profile = cast(Any, OrganizationFiscalProfile)
        row = (
            await session.execute(
                select(OrganizationFiscalProfile).where(
                    Profile.organization_id == organization_id
                )
            )
        ).scalar_one_or_none()
        return FiscalService._profile_response(row) if row else None

    @staticmethod
    async def upsert_profile(
        session: AsyncSession,
        organization_id: UUID,
        data: FiscalProfileUpsert,
    ) -> FiscalProfileResponse:
        Profile = cast(Any, OrganizationFiscalProfile)
        row = (
            await session.execute(
                select(OrganizationFiscalProfile).where(
                    Profile.organization_id == organization_id
                )
            )
        ).scalar_one_or_none()

        payload = data.model_dump()
        payload["identification_type"] = data.identification_type.value
        payload["country_code"] = data.country_code.upper()

        if row is None:
            row = OrganizationFiscalProfile(organization_id=organization_id, **payload)
            session.add(row)
        else:
            for key, value in payload.items():
                setattr(row, key, value)

        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.FISCAL_PROFILE_UPDATE,
            organization_id=organization_id,
            resource_type=AuditResourceType.FISCAL_PROFILE,
            resource_id=row.id,
            details={
                "identification_type": row.identification_type,
                "identification_number": row.identification_number,
                "legal_name": row.legal_name,
            },
        )
        await session.refresh(row)
        response = FiscalService._profile_response(row)
        await session.commit()
        return response

    @staticmethod
    async def get_credential_status(
        session: AsyncSession,
        organization_id: UUID,
    ) -> HaciendaCredentialStatusResponse:
        Cred = cast(Any, OrganizationHaciendaCredential)
        row = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(
                    Cred.organization_id == organization_id
                )
            )
        ).scalar_one_or_none()
        return FiscalService._credential_status(row)

    @staticmethod
    async def upsert_credentials(
        session: AsyncSession,
        organization_id: UUID,
        data: HaciendaCredentialUpsert,
        *,
        p12_bytes: Optional[bytes] = None,
    ) -> HaciendaCredentialStatusResponse:
        Cred = cast(Any, OrganizationHaciendaCredential)
        row = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(
                    Cred.organization_id == organization_id
                )
            )
        ).scalar_one_or_none()

        if row is None:
            row = OrganizationHaciendaCredential(
                organization_id=organization_id,
                environment=data.environment.value,
            )
            session.add(row)

        row.environment = data.environment.value
        if data.username is not None:
            row.username = data.username.strip() or None
        if data.oauth_client_id is not None:
            row.oauth_client_id = data.oauth_client_id.strip() or None
        if p12_bytes:
            row.p12_ciphertext = encrypt_bytes(p12_bytes)
        if data.p12_password is not None and data.p12_password != "":
            row.p12_password_ciphertext = encrypt_text(data.p12_password)
        if data.pin is not None and data.pin != "":
            row.pin_ciphertext = encrypt_text(data.pin)
        if data.oauth_client_secret is not None and data.oauth_client_secret != "":
            row.oauth_client_secret_ciphertext = encrypt_text(data.oauth_client_secret)

        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.HACIENDA_CREDENTIAL_UPDATE,
            organization_id=organization_id,
            resource_type=AuditResourceType.HACIENDA_CREDENTIAL,
            resource_id=row.id,
            details={
                "environment": row.environment,
                "has_p12": row.p12_ciphertext is not None,
                "has_username": bool(row.username),
            },
        )
        await session.refresh(row)
        response = FiscalService._credential_status(row)
        await session.commit()
        return response

    @staticmethod
    async def delete_credentials(
        session: AsyncSession,
        organization_id: UUID,
    ) -> HaciendaCredentialStatusResponse:
        Cred = cast(Any, OrganizationHaciendaCredential)
        row = (
            await session.execute(
                select(OrganizationHaciendaCredential).where(
                    Cred.organization_id == organization_id
                )
            )
        ).scalar_one_or_none()
        if row:
            resource_id = row.id
            await session.delete(row)
            await session.flush()
            await AuditService.record(
                session,
                action=AuditAction.HACIENDA_CREDENTIAL_DELETE,
                organization_id=organization_id,
                resource_type=AuditResourceType.HACIENDA_CREDENTIAL,
                resource_id=resource_id,
                details={},
            )
            await session.commit()
        return FiscalService._credential_status(None)
