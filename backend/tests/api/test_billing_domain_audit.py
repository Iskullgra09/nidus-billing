"""Assert critical billing/Hacienda domain actions land in audit_log."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient

from app.models.audit import AuditAction
from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
)


async def _actions(client: AsyncClient) -> set[str]:
    res = await client.get("/api/v1/audit-logs", params={"limit": 100})
    assert res.status_code == 200, res.text
    return {item["action"] for item in res.json()["data"]["items"]}


def _supplier_xml(*, clave: str) -> str:
    issued = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)
    return build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave=clave,
            consecutive="00100001010000000222",
            issued_at=issued,
            currency="CRC",
            exchange_rate=Decimal("1"),
            emitter=XmlParty(
                identification_type_code="02",
                identification_number="3101555123",
                name="Proveedor Audit SA",
                province="1",
                canton="01",
                district="01",
                email="prov@example.com",
                economic_activity_code="620100",
            ),
            receptor=XmlParty(
                identification_type_code="02",
                identification_number="3101123456",
                name="Acme Costa Rica SA",
                email="fiscal@acme.example",
            ),
            lines=[
                XmlLine(
                    number=1,
                    description="Audit line",
                    quantity=Decimal("1"),
                    unit="Unid",
                    unit_price=Decimal("100"),
                    subtotal=Decimal("100"),
                    tax_amount=Decimal("13"),
                    total=Decimal("113"),
                    tax_rate=Decimal("13"),
                    tax_code="08",
                    cabys_code="83119900",
                )
            ],
            subtotal=Decimal("100"),
            tax_total=Decimal("13"),
            total=Decimal("113"),
            payment_condition="contado",
        )
    )


@pytest.mark.asyncio
async def test_outbound_billing_writes_domain_audit(
    auth_client: tuple[AsyncClient, dict[str, Any]],
) -> None:
    client, _ = auth_client

    profile = await client.put(
        "/api/v1/billing/fiscal-profile",
        json={
            "legal_name": "Acme Costa Rica SA",
            "identification_type": "juridica",
            "identification_number": "3101123456",
            "economic_activity_code": "620100",
            "branch_code": "001",
            "province": "1",
            "canton": "01",
            "district": "01",
            "email": "fiscal@acme.example",
        },
    )
    assert profile.status_code == 200, profile.text

    customer = await client.post(
        "/api/v1/billing/customers",
        json={
            "name": "Audit Buyer",
            "email": "buyer@acme.example",
            "tax_id": "3101987654",
            "identification_type": "juridica",
        },
    )
    assert customer.status_code == 201, customer.text
    customer_id = customer.json()["data"]["id"]

    draft = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "CRC",
            "lines": [
                {
                    "description": "Service",
                    "quantity": "1",
                    "unit_price": "100",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    assert draft.status_code == 201, draft.text
    invoice_id = draft.json()["data"]["id"]

    issued = await client.post(f"/api/v1/billing/invoices/{invoice_id}/issue")
    assert issued.status_code == 200, issued.text

    sent = await client.post(f"/api/v1/billing/invoices/{invoice_id}/send-email", json={})
    assert sent.status_code == 201, sent.text

    emit = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert emit.status_code == 200, emit.text

    verify = await client.post(f"/api/v1/billing/invoices/{invoice_id}/verify-hacienda")
    assert verify.status_code == 200, verify.text

    actions = await _actions(client)
    for expected in (
        AuditAction.FISCAL_PROFILE_UPDATE,
        AuditAction.CUSTOMER_CREATE,
        AuditAction.INVOICE_CREATE,
        AuditAction.INVOICE_ISSUE,
        AuditAction.INVOICE_EMAIL_SEND,
        AuditAction.INVOICE_FISCAL_EMIT,
        AuditAction.INVOICE_FISCAL_VERIFY,
    ):
        assert expected.value in actions, f"missing audit action {expected.value}"


@pytest.mark.asyncio
async def test_inbound_and_mailbox_write_domain_audit(
    auth_client: tuple[AsyncClient, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import settings

    client, _ = auth_client
    monkeypatch.setattr(settings, "INBOUND_MAILBOX_DOMAIN", "compras.test.local")
    monkeypatch.setattr(settings, "INBOUND_MAILBOX_WEBHOOK_SECRET", "audit-mailbox-secret")

    await client.put(
        "/api/v1/billing/fiscal-profile",
        json={
            "legal_name": "Acme Costa Rica SA",
            "identification_type": "juridica",
            "identification_number": "3101123456",
            "economic_activity_code": "620100",
            "branch_code": "001",
            "province": "1",
            "canton": "01",
            "district": "01",
            "email": "fiscal@acme.example",
        },
    )

    mailbox = await client.get("/api/v1/billing/inbound-mailbox")
    assert mailbox.status_code == 200, mailbox.text
    address = mailbox.json()["data"]["address"]

    disabled = await client.put("/api/v1/billing/inbound-mailbox", json={"enabled": False})
    assert disabled.status_code == 200
    enabled = await client.put("/api/v1/billing/inbound-mailbox", json={"enabled": True})
    assert enabled.status_code == 200

    clave = "7" * 50
    created = await client.post(
        "/api/v1/billing/inbound-documents",
        json={"xml": _supplier_xml(clave=clave)},
    )
    assert created.status_code == 201, created.text
    document_id = created.json()["data"]["id"]

    accept = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/accept-hacienda"
    )
    assert accept.status_code == 200, accept.text

    verify = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/verify-hacienda"
    )
    assert verify.status_code == 200, verify.text

    # Second document via mailbox webhook (email channel)
    mail_clave = "8" * 50
    xml = _supplier_xml(clave=mail_clave)
    ingest = await client.post(
        "/api/v1/webhooks/inbound-mailbox",
        headers={"X-Nidus-Mailbox-Secret": "audit-mailbox-secret"},
        json={
            "to": address,
            "from": "supplier@example.com",
            "subject": "FE",
            "attachments": [{"filename": "fe.xml", "content": xml}],
        },
    )
    assert ingest.status_code == 200, ingest.text

    actions = await _actions(client)
    for expected in (
        AuditAction.INBOUND_MAILBOX_UPSERT,
        AuditAction.INBOUND_CREATE,
        AuditAction.INBOUND_ACCEPT,
        AuditAction.INBOUND_VERIFY,
    ):
        assert expected.value in actions, f"missing audit action {expected.value}"

    reject_clave = "9" * 50
    rejected_doc = await client.post(
        "/api/v1/billing/inbound-documents",
        json={"xml": _supplier_xml(clave=reject_clave)},
    )
    assert rejected_doc.status_code == 201, rejected_doc.text
    reject_id = rejected_doc.json()["data"]["id"]
    rejected = await client.post(
        f"/api/v1/billing/inbound-documents/{reject_id}/reject-hacienda",
        json={"reason": "Datos incorrectos del emisor"},
    )
    assert rejected.status_code == 200, rejected.text

    actions_after = await _actions(client)
    assert AuditAction.INBOUND_REJECT.value in actions_after
