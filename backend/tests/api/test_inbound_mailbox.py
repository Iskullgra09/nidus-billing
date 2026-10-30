from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from app.core.config import settings
from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
)


def _sample_supplier_xml(*, clave: str) -> str:
    issued = datetime(2026, 10, 30, 15, 0, tzinfo=timezone.utc)
    return build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave=clave,
            consecutive="00100001010000000101",
            issued_at=issued,
            currency="CRC",
            exchange_rate=Decimal("1"),
            emitter=XmlParty(
                identification_type_code="02",
                identification_number="3101555999",
                name="Proveedor Mailbox SA",
                province="1",
                canton="01",
                district="01",
                email="prov-mail@example.com",
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
                    description="Servicio email",
                    quantity=Decimal("1"),
                    unit="Unid",
                    unit_price=Decimal("50"),
                    subtotal=Decimal("50"),
                    tax_amount=Decimal("6.5"),
                    total=Decimal("56.5"),
                    tax_rate=Decimal("13"),
                    tax_code="08",
                    cabys_code="83119900",
                )
            ],
            subtotal=Decimal("50"),
            tax_total=Decimal("6.5"),
            total=Decimal("56.5"),
            payment_condition="contado",
        )
    )


@pytest.mark.asyncio
async def test_mailbox_provision_and_email_ingest(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
    monkeypatch: MonkeyPatch,
) -> None:
    client, _ = auth_client
    monkeypatch.setattr(settings, "INBOUND_MAILBOX_DOMAIN", "compras.test.local")
    monkeypatch.setattr(settings, "INBOUND_MAILBOX_WEBHOOK_SECRET", "test-mailbox-secret")

    mailbox = await client.get("/api/v1/billing/inbound-mailbox")
    assert mailbox.status_code == 200, mailbox.text
    data = mailbox.json()["data"]
    assert data["enabled"] is True
    assert data["domain"] == "compras.test.local"
    assert "@" in data["address"]
    assert data["address"].endswith("@compras.test.local")
    address = data["address"]

    disabled = await client.put("/api/v1/billing/inbound-mailbox", json={"enabled": False})
    assert disabled.status_code == 200
    assert disabled.json()["data"]["enabled"] is False

    enabled = await client.put("/api/v1/billing/inbound-mailbox", json={"enabled": True})
    assert enabled.status_code == 200
    assert enabled.json()["data"]["enabled"] is True

    clave = "6" * 50
    xml = _sample_supplier_xml(clave=clave)
    unauthorized = await client.post(
        "/api/v1/webhooks/inbound-mailbox",
        json={
            "to": address,
            "from": "supplier@example.com",
            "subject": "Factura electronica",
            "attachments": [{"filename": "fe.xml", "content": xml}],
        },
    )
    assert unauthorized.status_code == 401

    ingest = await client.post(
        "/api/v1/webhooks/inbound-mailbox",
        headers={"X-Nidus-Mailbox-Secret": "test-mailbox-secret"},
        json={
            "to": address,
            "from": "supplier@example.com",
            "subject": "Factura electronica",
            "attachments": [{"filename": "fe.xml", "content": xml}],
        },
    )
    assert ingest.status_code == 200, ingest.text
    body = ingest.json()["data"]
    assert body["clave"] == clave
    assert body["ingest_channel"] == "email"
    assert body["notes"] and "Imported from email" in body["notes"]

    listed = await client.get("/api/v1/billing/inbound-documents")
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert any(item["clave"] == clave and item["ingest_channel"] == "email" for item in items)

    # Idempotent retry for provider redelivery
    again = await client.post(
        "/api/v1/webhooks/inbound-mailbox",
        headers={"X-Nidus-Mailbox-Secret": "test-mailbox-secret"},
        json={
            "to": address,
            "from": "supplier@example.com",
            "subject": "Factura electronica",
            "attachments": [{"filename": "fe.xml", "content": xml}],
        },
    )
    assert again.status_code == 200, again.text
    assert again.json()["data"]["clave"] == clave
