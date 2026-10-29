from datetime import datetime, timezone
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError, EntityNotFoundError
from app.core.pagination import paginate_with_cursor
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.customer import Customer
from app.models.billing.supplier import Supplier
from app.schemas.filters.billing import PartyFilter
from app.schemas.requests.billing import PartyCreate, PartyUpdate
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.billing import PartyResponse
from app.schemas.responses.pagination import CursorPage, PageInfo
from app.services.audit_service import AuditService

PartyModelT = TypeVar("PartyModelT", Customer, Supplier)


def _to_party_response(row: Customer | Supplier) -> PartyResponse:
    return PartyResponse.model_validate(row)


class _PartyCRUD:
    def __init__(
        self,
        *,
        model: type[PartyModelT],
        resource_type: AuditResourceType,
        create_action: AuditAction,
        update_action: AuditAction,
        delete_action: AuditAction,
        tax_conflict_key: str,
    ) -> None:
        self.model = model
        self.resource_type = resource_type
        self.create_action = create_action
        self.update_action = update_action
        self.delete_action = delete_action
        self.tax_conflict_key = tax_conflict_key

    async def list(
        self,
        session: AsyncSession,
        pagination: CursorParams,
        filters: PartyFilter,
    ) -> CursorPage[PartyResponse]:
        Model = cast(Any, self.model)
        stmt = select(self.model).where(Model.deleted_at.is_(None))

        if filters.q:
            term = f"%{filters.q.strip()}%"
            stmt = stmt.where(
                or_(
                    Model.name.ilike(term),
                    Model.email.ilike(term),
                    Model.tax_id.ilike(term),
                )
            )
        if filters.is_active is not None:
            stmt = stmt.where(Model.is_active == filters.is_active)

        items, end_cursor, has_next = await paginate_with_cursor(
            session=session,
            stmt=stmt,
            model_class=Model,
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
        return CursorPage(
            items=[_to_party_response(row) for row in items],
            page_info=PageInfo(has_next_page=has_next, end_cursor=end_cursor),
        )

    async def _assert_tax_id_unique(
        self,
        session: AsyncSession,
        org_id: UUID,
        tax_id: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if not tax_id:
            return
        Model = cast(Any, self.model)
        stmt = select(self.model).where(
            Model.organization_id == org_id,
            Model.tax_id == tax_id,
            Model.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(Model.id != exclude_id)
        if (await session.execute(stmt)).scalar_one_or_none():
            raise ConflictError(message_key=self.tax_conflict_key, tax_id=tax_id)

    async def create(self, session: AsyncSession, org_id: UUID, data: PartyCreate) -> PartyResponse:
        await self._assert_tax_id_unique(session, org_id, data.tax_id)
        row = self.model(
            organization_id=org_id,
            name=data.name.strip(),
            email=str(data.email) if data.email else None,
            phone=data.phone,
            tax_id=data.tax_id.strip() if data.tax_id else None,
            notes=data.notes,
            is_active=data.is_active,
        )
        session.add(row)
        await session.flush()
        await AuditService.record(
            session,
            action=self.create_action,
            organization_id=org_id,
            resource_type=self.resource_type,
            resource_id=row.id,
            details={"name": row.name},
        )
        await session.refresh(row)
        response = _to_party_response(row)
        await session.commit()
        return response

    async def get(self, session: AsyncSession, party_id: UUID) -> PartyResponse:
        Model = cast(Any, self.model)
        stmt = select(self.model).where(Model.id == party_id, Model.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity=self.resource_type.value)
        return _to_party_response(row)

    async def update(self, session: AsyncSession, party_id: UUID, data: PartyUpdate) -> PartyResponse:
        Model = cast(Any, self.model)
        stmt = select(self.model).where(Model.id == party_id, Model.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity=self.resource_type.value)

        payload = data.model_dump(exclude_unset=True)
        if "tax_id" in payload:
            tax_id = payload["tax_id"].strip() if payload["tax_id"] else None
            await self._assert_tax_id_unique(session, row.organization_id, tax_id, exclude_id=party_id)
            row.tax_id = tax_id
            del payload["tax_id"]
        if "name" in payload and payload["name"] is not None:
            row.name = payload["name"].strip()
            del payload["name"]
        if "email" in payload:
            row.email = str(payload["email"]) if payload["email"] else None
            del payload["email"]
        for key, value in payload.items():
            setattr(row, key, value)

        await AuditService.record(
            session,
            action=self.update_action,
            organization_id=row.organization_id,
            resource_type=self.resource_type,
            resource_id=row.id,
            details={"name": row.name},
        )
        await session.flush()
        await session.refresh(row)
        response = _to_party_response(row)
        await session.commit()
        return response

    async def delete(self, session: AsyncSession, party_id: UUID) -> None:
        Model = cast(Any, self.model)
        stmt = select(self.model).where(Model.id == party_id, Model.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity=self.resource_type.value)

        row.deleted_at = datetime.now(timezone.utc)
        await AuditService.record(
            session,
            action=self.delete_action,
            organization_id=row.organization_id,
            resource_type=self.resource_type,
            resource_id=row.id,
            details={"name": row.name},
        )
        await session.commit()


class CustomerService:
    _crud = _PartyCRUD(
        model=Customer,
        resource_type=AuditResourceType.CUSTOMER,
        create_action=AuditAction.CUSTOMER_CREATE,
        update_action=AuditAction.CUSTOMER_UPDATE,
        delete_action=AuditAction.CUSTOMER_DELETE,
        tax_conflict_key="billing.customer_tax_id_conflict",
    )

    @staticmethod
    async def list_customers(
        session: AsyncSession, pagination: CursorParams, filters: PartyFilter
    ) -> CursorPage[PartyResponse]:
        return await CustomerService._crud.list(session, pagination, filters)

    @staticmethod
    async def create_customer(session: AsyncSession, org_id: UUID, data: PartyCreate) -> PartyResponse:
        return await CustomerService._crud.create(session, org_id, data)

    @staticmethod
    async def get_customer(session: AsyncSession, customer_id: UUID) -> PartyResponse:
        return await CustomerService._crud.get(session, customer_id)

    @staticmethod
    async def update_customer(session: AsyncSession, customer_id: UUID, data: PartyUpdate) -> PartyResponse:
        return await CustomerService._crud.update(session, customer_id, data)

    @staticmethod
    async def delete_customer(session: AsyncSession, customer_id: UUID) -> None:
        await CustomerService._crud.delete(session, customer_id)


class SupplierService:
    _crud = _PartyCRUD(
        model=Supplier,
        resource_type=AuditResourceType.SUPPLIER,
        create_action=AuditAction.SUPPLIER_CREATE,
        update_action=AuditAction.SUPPLIER_UPDATE,
        delete_action=AuditAction.SUPPLIER_DELETE,
        tax_conflict_key="billing.supplier_tax_id_conflict",
    )

    @staticmethod
    async def list_suppliers(
        session: AsyncSession, pagination: CursorParams, filters: PartyFilter
    ) -> CursorPage[PartyResponse]:
        return await SupplierService._crud.list(session, pagination, filters)

    @staticmethod
    async def create_supplier(session: AsyncSession, org_id: UUID, data: PartyCreate) -> PartyResponse:
        return await SupplierService._crud.create(session, org_id, data)

    @staticmethod
    async def get_supplier(session: AsyncSession, supplier_id: UUID) -> PartyResponse:
        return await SupplierService._crud.get(session, supplier_id)

    @staticmethod
    async def update_supplier(session: AsyncSession, supplier_id: UUID, data: PartyUpdate) -> PartyResponse:
        return await SupplierService._crud.update(session, supplier_id, data)

    @staticmethod
    async def delete_supplier(session: AsyncSession, supplier_id: UUID) -> None:
        await SupplierService._crud.delete(session, supplier_id)
