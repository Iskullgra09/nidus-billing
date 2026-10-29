from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient

from app.services.billing.hacienda.clave import build_clave, build_consecutive


def test_build_clave_is_fifty_digits() -> None:
    consecutive = build_consecutive(
        branch_code="001",
        document_type="01",
        sequence=42,
    )
    assert consecutive == "00100001010000000042"
    clave = build_clave(
        issued_at=datetime(2026, 10, 29, 15, 0, tzinfo=timezone.utc),
        emitter_id="3101123456",
        consecutive=consecutive,
        security_code="12345678",
    )
    assert len(clave) == 50
    assert clave.isdigit()
    assert clave.startswith("506291026")
    assert clave.endswith("112345678")


@pytest.mark.asyncio
async def test_emit_and_verify_hacienda_mock(
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

    customer_res = await client.post(
        "/api/v1/billing/customers",
        json={
            "name": "Fiscal Client",
            "email": "client@acme.example",
            "tax_id": "3101987654",
            "identification_type": "juridica",
        },
    )
    assert customer_res.status_code == 201
    customer_id = customer_res.json()["data"]["id"]

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
                    "unit_price": "100.0000",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    assert draft.status_code == 201, draft.text
    invoice_id = draft.json()["data"]["id"]
    assert draft.json()["data"]["currency"] == "CRC"
    assert draft.json()["data"]["lines"][0]["cabys_code"] == "85171200"

    blocked_draft = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda"
    )
    assert blocked_draft.status_code == 400

    issued = await client.post(f"/api/v1/billing/invoices/{invoice_id}/issue")
    assert issued.status_code == 200

    empty_fiscal = await client.get(f"/api/v1/billing/invoices/{invoice_id}/fiscal")
    assert empty_fiscal.status_code == 200
    assert empty_fiscal.json()["data"] is None

    emit = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert emit.status_code == 200, emit.text
    fiscal = emit.json()["data"]
    assert fiscal["status"] == "submitted"
    assert fiscal["mock_mode"] is True
    assert fiscal["clave"] and len(fiscal["clave"]) == 50
    assert fiscal["consecutive"]

    again = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert again.status_code == 409

    verify = await client.post(f"/api/v1/billing/invoices/{invoice_id}/verify-hacienda")
    assert verify.status_code == 200, verify.text
    verified = verify.json()["data"]
    assert verified["status"] == "accepted"
    assert verified["clave"] == fiscal["clave"]

    got = await client.get(f"/api/v1/billing/invoices/{invoice_id}/fiscal")
    assert got.status_code == 200
    assert got.json()["data"]["status"] == "accepted"


@pytest.mark.asyncio
async def test_emit_requires_cabys(
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
    customer_res = await client.post(
        "/api/v1/billing/customers",
        json={"name": "No Cabys", "tax_id": "3101987001"},
    )
    customer_id = customer_res.json()["data"]["id"]
    draft = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "CRC",
            "lines": [
                {
                    "description": "Missing CABYS",
                    "quantity": "1",
                    "unit_price": "10",
                    "tax_rate": "13",
                }
            ],
        },
    )
    invoice_id = draft.json()["data"]["id"]
    await client.post(f"/api/v1/billing/invoices/{invoice_id}/issue")
    emit = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert emit.status_code == 400
    assert emit.json()["code"] == "CABYS_REQUIRED"


@pytest.mark.asyncio
async def test_emit_usd_requires_exchange_rate(
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
    customer_res = await client.post(
        "/api/v1/billing/customers",
        json={"name": "USD Client", "tax_id": "3101987002"},
    )
    customer_id = customer_res.json()["data"]["id"]

    missing_rate = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "USD",
            "lines": [
                {
                    "description": "USD no rate",
                    "quantity": "1",
                    "unit_price": "10",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    assert missing_rate.status_code == 201
    missing_id = missing_rate.json()["data"]["id"]
    await client.post(f"/api/v1/billing/invoices/{missing_id}/issue")
    blocked = await client.post(f"/api/v1/billing/invoices/{missing_id}/emit-hacienda")
    assert blocked.status_code == 400
    assert blocked.json()["code"] == "EXCHANGE_RATE_REQUIRED"

    with_rate = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "USD",
            "exchange_rate": "520.00000",
            "exchange_rate_date": "2026-10-29",
            "lines": [
                {
                    "description": "USD with rate",
                    "quantity": "1",
                    "unit_price": "10",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    assert with_rate.status_code == 201, with_rate.text
    assert with_rate.json()["data"]["exchange_rate"] == "520.00000"
    rate_id = with_rate.json()["data"]["id"]
    await client.post(f"/api/v1/billing/invoices/{rate_id}/issue")
    emit = await client.post(f"/api/v1/billing/invoices/{rate_id}/emit-hacienda")
    assert emit.status_code == 200, emit.text
    assert emit.json()["data"]["mock_mode"] is True


@pytest.mark.asyncio
async def test_currency_whitelist(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client
    customer_res = await client.post(
        "/api/v1/billing/customers",
        json={"name": "USD Co", "tax_id": "3101111222"},
    )
    customer_id = customer_res.json()["data"]["id"]

    ok = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "USD",
            "exchange_rate": "500.00000",
            "lines": [
                {
                    "description": "USD line",
                    "quantity": "1",
                    "unit_price": "10",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    assert ok.status_code == 201
    assert ok.json()["data"]["currency"] == "USD"

    bad = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "currency": "EUR",
            "lines": [{"description": "EUR line", "quantity": "1", "unit_price": "10"}],
        },
    )
    assert bad.status_code == 422
