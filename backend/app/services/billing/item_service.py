from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError, EntityNotFoundError
from app.core.pagination import paginate_with_cursor
from app.models.audit import AuditAction, AuditResourceType
from app.models.billing.item import Item
from app.schemas.filters.billing import ItemFilter
from app.schemas.requests.billing import ItemCreate, ItemUpdate
from app.schemas.requests.pagination import CursorParams
from app.schemas.responses.billing import ItemResponse
from app.schemas.responses.pagination import CursorPage, PageInfo
from app.services.audit_service import AuditService


class ItemService:
    @staticmethod
    def _to_response(row: Item) -> ItemResponse:
        return ItemResponse.model_validate(row)

    @staticmethod
    async def _assert_sku_unique(
        session: AsyncSession,
        org_id: UUID,
        sku: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if not sku:
            return
        ItemModel = cast(Any, Item)
        stmt = select(Item).where(
            ItemModel.organization_id == org_id,
            ItemModel.sku == sku,
            ItemModel.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(ItemModel.id != exclude_id)
        if (await session.execute(stmt)).scalar_one_or_none():
            raise ConflictError(message_key="billing.item_sku_conflict", sku=sku)

    @staticmethod
    async def list_items(
        session: AsyncSession,
        pagination: CursorParams,
        filters: ItemFilter,
    ) -> CursorPage[ItemResponse]:
        ItemModel = cast(Any, Item)
        stmt = select(Item).where(ItemModel.deleted_at.is_(None))

        if filters.q:
            term = f"%{filters.q.strip()}%"
            stmt = stmt.where(or_(ItemModel.name.ilike(term), ItemModel.sku.ilike(term)))
        if filters.is_active is not None:
            stmt = stmt.where(ItemModel.is_active == filters.is_active)
        if filters.is_service is not None:
            stmt = stmt.where(ItemModel.is_service == filters.is_service)

        items, end_cursor, has_next = await paginate_with_cursor(
            session=session,
            stmt=stmt,
            model_class=ItemModel,
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
        return CursorPage(
            items=[ItemService._to_response(row) for row in items],
            page_info=PageInfo(has_next_page=has_next, end_cursor=end_cursor),
        )

    @staticmethod
    async def create_item(session: AsyncSession, org_id: UUID, data: ItemCreate) -> ItemResponse:
        sku = data.sku.strip() if data.sku else None
        await ItemService._assert_sku_unique(session, org_id, sku)
        row = Item(
            organization_id=org_id,
            sku=sku,
            name=data.name.strip(),
            description=data.description,
            unit=data.unit.strip(),
            unit_price=data.unit_price,
            tax_rate=data.tax_rate,
            cabys_code=data.cabys_code.strip() if data.cabys_code else None,
            is_service=data.is_service,
            is_active=data.is_active,
        )
        session.add(row)
        await session.flush()
        await AuditService.record(
            session,
            action=AuditAction.ITEM_CREATE,
            organization_id=org_id,
            resource_type=AuditResourceType.ITEM,
            resource_id=row.id,
            details={"name": row.name, "sku": row.sku},
        )
        await session.refresh(row)
        response = ItemService._to_response(row)
        await session.commit()
        return response

    @staticmethod
    async def get_item(session: AsyncSession, item_id: UUID) -> ItemResponse:
        ItemModel = cast(Any, Item)
        stmt = select(Item).where(ItemModel.id == item_id, ItemModel.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity="item")
        return ItemService._to_response(row)

    @staticmethod
    async def update_item(session: AsyncSession, item_id: UUID, data: ItemUpdate) -> ItemResponse:
        ItemModel = cast(Any, Item)
        stmt = select(Item).where(ItemModel.id == item_id, ItemModel.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity="item")

        payload = data.model_dump(exclude_unset=True)
        if "sku" in payload:
            sku = payload["sku"].strip() if payload["sku"] else None
            await ItemService._assert_sku_unique(session, row.organization_id, sku, exclude_id=item_id)
            row.sku = sku
            del payload["sku"]
        if "name" in payload and payload["name"] is not None:
            row.name = payload["name"].strip()
            del payload["name"]
        if "unit" in payload and payload["unit"] is not None:
            row.unit = payload["unit"].strip()
            del payload["unit"]
        if "cabys_code" in payload:
            cabys = payload["cabys_code"]
            row.cabys_code = cabys.strip() if cabys else None
            del payload["cabys_code"]
        for key, value in payload.items():
            setattr(row, key, value)

        await AuditService.record(
            session,
            action=AuditAction.ITEM_UPDATE,
            organization_id=row.organization_id,
            resource_type=AuditResourceType.ITEM,
            resource_id=row.id,
            details={"name": row.name, "sku": row.sku},
        )
        await session.flush()
        await session.refresh(row)
        response = ItemService._to_response(row)
        await session.commit()
        return response

    @staticmethod
    async def delete_item(session: AsyncSession, item_id: UUID) -> None:
        ItemModel = cast(Any, Item)
        stmt = select(Item).where(ItemModel.id == item_id, ItemModel.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(entity="item")

        row.deleted_at = datetime.now(timezone.utc)
        await AuditService.record(
            session,
            action=AuditAction.ITEM_DELETE,
            organization_id=row.organization_id,
            resource_type=AuditResourceType.ITEM,
            resource_id=row.id,
            details={"name": row.name, "sku": row.sku},
        )
        await session.commit()
