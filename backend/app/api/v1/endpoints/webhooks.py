from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.i18n.service import i18n
from app.core.rate_limit import RateLimit
from app.core.request_context import RequestContext
from app.schemas.requests.billing import InboundMailboxWebhookPayload
from app.schemas.responses.base import GenericResponse
from app.schemas.responses.billing import InboundDocumentResponse
from app.services.billing import InboundMailboxService

router = APIRouter()


@router.post(
    "/inbound-mailbox",
    response_model=GenericResponse[InboundDocumentResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimit("webhooks.inbound_mailbox", tier="strict"))],
)
async def inbound_mailbox_webhook(
    body: InboundMailboxWebhookPayload,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_nidus_mailbox_secret: Optional[str] = Header(default=None, alias="X-Nidus-Mailbox-Secret"),
):
    """Ingest supplier FE XML emailed/forwarded to a per-org purchase mailbox."""
    InboundMailboxService.verify_webhook_secret(x_nidus_mailbox_secret)
    data = await InboundMailboxService.ingest_webhook(
        session,
        body,
        ip_address=RequestContext.get_client_ip() or (request.client.host if request.client else None),
    )
    return GenericResponse(
        data=data,
        message=i18n.t("success.inbound_mailbox_ingested", lang="en"),
    )
