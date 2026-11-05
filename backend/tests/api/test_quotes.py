from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient

from app.models.audit import AuditAction


@pytest.mark.asyncio
async def test_quote_crud_mark_sent_and_convert(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client

    customer = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Quote Buyer", "email": "quote@acme.example", "tax_id": "3101999001"},
    )
    assert customer.status_code == 201, customer.text
    customer_id = customer.json()["data"]["id"]

    created = await client.post(
        "/api/v1/billing/quotes",
        json={
            "customer_id": customer_id,
            "currency": "CRC",
            "reference_number": "Q-100",
            "notes": "Pilot quote",
            "lines": [
                {
                    "description": "Consulting",
                    "quantity": "2",
                    "unit_price": "50",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                    "unit": "hour",
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    quote = created.json()["data"]
    quote_id = quote["id"]
    assert quote["status"] == "draft"
    assert quote["total"] == "113.0000"
    assert len(quote["lines"]) == 1

    listed = await client.get("/api/v1/billing/quotes", params={"q": "Q-100"})
    assert listed.status_code == 200
    assert any(item["id"] == quote_id for item in listed.json()["data"]["items"])

    sent = await client.post(f"/api/v1/billing/quotes/{quote_id}/mark-sent")
    assert sent.status_code == 200, sent.text
    assert sent.json()["data"]["status"] == "sent"

    converted = await client.post(f"/api/v1/billing/quotes/{quote_id}/convert")
    assert converted.status_code == 200, converted.text
    invoice = converted.json()["data"]
    assert invoice["status"] == "draft"
    assert invoice["customer_id"] == customer_id
    assert invoice["total"] == "113.0000"
    assert len(invoice["lines"]) == 1
    assert invoice["lines"][0]["description"] == "Consulting"
    assert invoice["lines"][0]["cabys_code"] == "85171200"

    got = await client.get(f"/api/v1/billing/quotes/{quote_id}")
    assert got.status_code == 200
    body = got.json()["data"]
    assert body["status"] == "converted"
    assert body["converted_invoice_id"] == invoice["id"]

    again = await client.post(f"/api/v1/billing/quotes/{quote_id}/convert")
    assert again.status_code == 409
    assert again.json()["code"] == "QUOTE_ALREADY_CONVERTED"

    logs = await client.get(
        "/api/v1/audit-logs",
        params={"action": AuditAction.QUOTE_CONVERT.value},
    )
    assert logs.status_code == 200
    assert any(item["resource_id"] == quote_id for item in logs.json()["data"]["items"])


@pytest.mark.asyncio
async def test_quote_delete_draft(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client
    customer = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Temp Quote Co"},
    )
    customer_id = customer.json()["data"]["id"]
    created = await client.post(
        "/api/v1/billing/quotes",
        json={
            "customer_id": customer_id,
            "lines": [{"description": "Line", "quantity": "1", "unit_price": "10"}],
        },
    )
    quote_id = created.json()["data"]["id"]
    deleted = await client.delete(f"/api/v1/billing/quotes/{quote_id}")
    assert deleted.status_code == 200
    missing = await client.get(f"/api/v1/billing/quotes/{quote_id}")
    assert missing.status_code == 404
