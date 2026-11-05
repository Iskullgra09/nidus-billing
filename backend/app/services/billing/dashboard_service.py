from decimal import Decimal
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing.enums import HaciendaFiscalStatus, InvoiceStatus
from app.models.billing.invoice import Invoice
from app.models.billing.invoice_fiscal import InvoiceFiscal
from app.schemas.responses.billing import (
    DashboardEmitItem,
    DashboardFailureItem,
    DashboardSummaryResponse,
)
from app.services.billing.hacienda import humanize_mh_message

MONEY = Decimal("0.0001")


class DashboardService:
    @staticmethod
    async def get_summary(session: AsyncSession, *, emit_limit: int = 5) -> DashboardSummaryResponse:
        InvoiceModel = cast(Any, Invoice)
        Fiscal = cast(Any, InvoiceFiscal)

        open_statuses = (InvoiceStatus.ISSUED.value, InvoiceStatus.PARTIAL.value)
        open_ar_row = (
            await session.execute(
                select(
                    func.coalesce(func.sum(InvoiceModel.balance_due), 0),
                    func.count(InvoiceModel.id),
                ).where(
                    InvoiceModel.deleted_at.is_(None),
                    InvoiceModel.status.in_(open_statuses),
                    InvoiceModel.currency == "CRC",
                )
            )
        ).one()
        open_ar = Decimal(str(open_ar_row[0])).quantize(MONEY)
        open_count = int(open_ar_row[1] or 0)

        emit_rows = (
            await session.execute(
                select(Fiscal)
                .order_by(Fiscal.updated_at.desc(), Fiscal.id.desc())
                .limit(emit_limit)
            )
        ).scalars().all()
        recent_emits = [
            DashboardEmitItem(
                invoice_id=row.invoice_id,
                clave=row.clave,
                status=row.status,
                updated_at=row.updated_at,
            )
            for row in emit_rows
        ]

        failure_statuses = (
            HaciendaFiscalStatus.REJECTED.value,
            HaciendaFiscalStatus.ERROR.value,
        )
        failure_count = int(
            (
                await session.execute(
                    select(func.count(Fiscal.id)).where(Fiscal.status.in_(failure_statuses))
                )
            ).scalar_one()
            or 0
        )
        failure_rows = (
            await session.execute(
                select(Fiscal)
                .where(Fiscal.status.in_(failure_statuses))
                .order_by(Fiscal.updated_at.desc(), Fiscal.id.desc())
                .limit(emit_limit)
            )
        ).scalars().all()
        hacienda_failures = [
            DashboardFailureItem(
                invoice_id=row.invoice_id,
                clave=row.clave,
                status=row.status,
                message=humanize_mh_message(row.mh_message)
                or humanize_mh_message(row.mh_response_xml),
                updated_at=row.updated_at,
            )
            for row in failure_rows
        ]

        return DashboardSummaryResponse(
            open_ar=open_ar,
            open_ar_currency="CRC",
            open_invoice_count=open_count,
            recent_emits=recent_emits,
            hacienda_failure_count=failure_count,
            hacienda_failures=hacienda_failures,
        )
