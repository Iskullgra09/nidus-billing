from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_open_ar_and_emits(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client

    empty = await client.get("/api/v1/billing/dashboard-summary")
    assert empty.status_code == 200, empty.text
    empty_body = empty.json()["data"]
    assert empty_body["open_ar"] == "0.0000"
    assert empty_body["open_invoice_count"] == 0
    assert empty_body["recent_emits"] == []
    assert empty_body["hacienda_failure_count"] == 0

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
    customer = await client.post(
        "/api/v1/billing/customers",
        json={"name": "AR Client", "tax_id": "3101888111"},
    )
    customer_id = customer.json()["data"]["id"]
    draft = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "credito",
            "currency": "CRC",
            "due_date": "2030-01-15",
            "lines": [
                {
                    "description": "AR line",
                    "quantity": "1",
                    "unit_price": "100",
                    "tax_rate": "13",
                    "cabys_code": "85171200",
                }
            ],
        },
    )
    invoice_id = draft.json()["data"]["id"]
    await client.post(f"/api/v1/billing/invoices/{invoice_id}/issue")
    emit = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert emit.status_code == 200, emit.text

    summary = await client.get("/api/v1/billing/dashboard-summary")
    assert summary.status_code == 200, summary.text
    body = summary.json()["data"]
    assert body["open_invoice_count"] == 1
    assert body["open_ar"] == "113.0000"
    assert body["open_ar_currency"] == "CRC"
    assert any(item["invoice_id"] == invoice_id for item in body["recent_emits"])
