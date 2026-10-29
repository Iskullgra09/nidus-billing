from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_crud(auth_client: Tuple[AsyncClient, Dict[str, Any]]) -> None:
    client, _ = auth_client

    create_res = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Acme Retail", "email": "retail@acme.example", "tax_id": "3101000001"},
    )
    assert create_res.status_code == 201
    customer_id = create_res.json()["data"]["id"]
    assert create_res.json()["data"]["name"] == "Acme Retail"

    list_res = await client.get("/api/v1/billing/customers", params={"q": "Acme"})
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]["items"]) == 1

    patch_res = await client.patch(
        f"/api/v1/billing/customers/{customer_id}",
        json={"phone": "+50688880000"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["phone"] == "+50688880000"

    conflict = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Other", "tax_id": "3101000001"},
    )
    assert conflict.status_code == 409

    delete_res = await client.delete(f"/api/v1/billing/customers/{customer_id}")
    assert delete_res.status_code == 200

    empty = await client.get("/api/v1/billing/customers", params={"q": "Acme"})
    assert empty.status_code == 200
    assert empty.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_supplier_and_item_crud(auth_client: Tuple[AsyncClient, Dict[str, Any]]) -> None:
    client, _ = auth_client

    supplier_res = await client.post(
        "/api/v1/billing/suppliers",
        json={"name": "Office Supplies CR", "tax_id": "3101999999"},
    )
    assert supplier_res.status_code == 201

    item_res = await client.post(
        "/api/v1/billing/items",
        json={
            "name": "Consulting hour",
            "sku": "SRV-001",
            "unit": "hour",
            "unit_price": "75.5000",
            "tax_rate": "13",
            "is_service": True,
        },
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["data"]["id"]
    assert item_res.json()["data"]["is_service"] is True

    sku_conflict = await client.post(
        "/api/v1/billing/items",
        json={"name": "Other", "sku": "SRV-001", "unit_price": "10"},
    )
    assert sku_conflict.status_code == 409

    list_items = await client.get("/api/v1/billing/items", params={"is_service": True})
    assert list_items.status_code == 200
    assert len(list_items.json()["data"]["items"]) == 1

    delete_item = await client.delete(f"/api/v1/billing/items/{item_id}")
    assert delete_item.status_code == 200


@pytest.mark.asyncio
async def test_invoice_lifecycle_and_pdf(auth_client: Tuple[AsyncClient, Dict[str, Any]]) -> None:
    client, _ = auth_client

    customer_res = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Invoice Buyer", "email": "buyer@acme.example"},
    )
    assert customer_res.status_code == 201
    customer_id = customer_res.json()["data"]["id"]

    item_res = await client.post(
        "/api/v1/billing/items",
        json={"name": "Widget", "sku": "W-1", "unit_price": "100.0000", "tax_rate": "13"},
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["data"]["id"]

    create_res = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "reference_number": "TMP-001",
            "lines": [
                {
                    "item_id": item_id,
                    "description": "Widget",
                    "quantity": "2",
                    "unit_price": "100.0000",
                    "tax_rate": "13",
                }
            ],
        },
    )
    assert create_res.status_code == 201
    invoice = create_res.json()["data"]
    invoice_id = invoice["id"]
    assert invoice["status"] == "draft"
    assert invoice["total"] == "226.0000"
    assert len(invoice["lines"]) == 1

    issue_res = await client.post(f"/api/v1/billing/invoices/{invoice_id}/issue")
    assert issue_res.status_code == 200
    issued = issue_res.json()["data"]
    assert issued["status"] == "issued"
    assert issued["document_number"] == "INV-000001"
    assert issued["balance_due"] == "226.0000"

    patch_blocked = await client.patch(
        f"/api/v1/billing/invoices/{invoice_id}",
        json={"notes": "nope"},
    )
    assert patch_blocked.status_code == 400

    pay_res = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        json={"amount": "100.0000", "method": "transfer"},
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["data"]["status"] == "partial"
    assert pay_res.json()["data"]["amount_paid"] == "100.0000"

    void_blocked = await client.post(f"/api/v1/billing/invoices/{invoice_id}/void")
    assert void_blocked.status_code == 400

    pay_full = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        json={"amount": "126.0000", "method": "cash"},
    )
    assert pay_full.status_code == 201
    assert pay_full.json()["data"]["status"] == "paid"
    assert pay_full.json()["data"]["balance_due"] == "0.0000"

    pdf_res = await client.get(f"/api/v1/billing/invoices/{invoice_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"].startswith("application/pdf")
    assert pdf_res.content[:4] == b"%PDF"

    # Separate invoice to exercise void without payments
    voidable = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "contado",
            "lines": [{"description": "One-off", "quantity": "1", "unit_price": "10"}],
        },
    )
    voidable_id = voidable.json()["data"]["id"]
    await client.post(f"/api/v1/billing/invoices/{voidable_id}/issue")
    void_res = await client.post(f"/api/v1/billing/invoices/{voidable_id}/void")
    assert void_res.status_code == 200
    assert void_res.json()["data"]["status"] == "void"
    assert void_res.json()["data"]["document_number"] == "INV-000002"

    credit_draft = await client.post(
        "/api/v1/billing/invoices",
        json={
            "customer_id": customer_id,
            "payment_condition": "credito",
            "lines": [{"description": "Service", "quantity": "1", "unit_price": "50"}],
        },
    )
    assert credit_draft.status_code == 201
    credit_id = credit_draft.json()["data"]["id"]
    missing_due = await client.post(f"/api/v1/billing/invoices/{credit_id}/issue")
    assert missing_due.status_code == 400

    with_due = await client.patch(
        f"/api/v1/billing/invoices/{credit_id}",
        json={"due_date": "2026-12-31"},
    )
    assert with_due.status_code == 200
    issued_credit = await client.post(f"/api/v1/billing/invoices/{credit_id}/issue")
    assert issued_credit.status_code == 200
    assert issued_credit.json()["data"]["status"] == "issued"
