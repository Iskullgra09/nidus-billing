from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient

from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
)


def _sample_supplier_xml(*, clave: str = "5" * 50) -> str:
    issued = datetime(2026, 10, 29, 15, 0, tzinfo=timezone.utc)
    return build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave=clave,
            consecutive="00100001010000000099",
            issued_at=issued,
            currency="CRC",
            exchange_rate=Decimal("1"),
            emitter=XmlParty(
                identification_type_code="02",
                identification_number="3101555123",
                name="Proveedor Seed SA",
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
                    description="Servicio",
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
async def test_inbound_upload_accept_verify_mock(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
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
            "province": "San José",
            "canton": "Central",
            "district": "Carmen",
            "email": "fiscal@acme.example",
        },
    )
    assert profile.status_code == 200, profile.text

    supplier = await client.post(
        "/api/v1/billing/suppliers",
        json={
            "name": "Proveedor Seed SA",
            "tax_id": "3101555123",
            "identification_type": "juridica",
        },
    )
    assert supplier.status_code == 201, supplier.text
    supplier_id = supplier.json()["data"]["id"]

    created = await client.post(
        "/api/v1/billing/inbound-documents",
        json={"xml": _sample_supplier_xml()},
    )
    assert created.status_code == 201, created.text
    doc = created.json()["data"]
    assert doc["status"] == "pending"
    assert doc["clave"] == "5" * 50
    assert doc["supplier_id"] == supplier_id
    assert doc["emitter_name"] == "Proveedor Seed SA"
    document_id = doc["id"]

    dup = await client.post(
        "/api/v1/billing/inbound-documents",
        json={"xml": _sample_supplier_xml()},
    )
    assert dup.status_code == 409

    listed = await client.get("/api/v1/billing/inbound-documents")
    assert listed.status_code == 200
    assert any(item["id"] == document_id for item in listed.json()["data"]["items"])

    accept = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/accept-hacienda"
    )
    assert accept.status_code == 200, accept.text
    assert accept.json()["data"]["status"] == "submitted"
    assert accept.json()["data"]["mensaje_tipo"] == "1"
    assert accept.json()["data"]["mock_mode"] is True

    again = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/accept-hacienda"
    )
    assert again.status_code == 409

    verify = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/verify-hacienda"
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["data"]["status"] == "accepted"


@pytest.mark.asyncio
async def test_inbound_reject_requires_reason(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client
    await client.put(
        "/api/v1/billing/fiscal-profile",
        json={
            "legal_name": "Acme Costa Rica SA",
            "identification_type": "juridica",
            "identification_number": "3101123456",
            "economic_activity_code": "620100",
            "branch_code": "001",
            "province": "San José",
            "canton": "Central",
            "district": "Carmen",
            "email": "fiscal@acme.example",
        },
    )
    clave = "6" * 50
    created = await client.post(
        "/api/v1/billing/inbound-documents",
        json={"xml": _sample_supplier_xml(clave=clave)},
    )
    document_id = created.json()["data"]["id"]

    bad = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/reject-hacienda",
        json={"reason": "no"},
    )
    assert bad.status_code == 422

    rejected = await client.post(
        f"/api/v1/billing/inbound-documents/{document_id}/reject-hacienda",
        json={"reason": "Datos incorrectos del emisor"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["data"]["mensaje_tipo"] == "3"
    assert rejected.json()["data"]["status"] == "submitted"
