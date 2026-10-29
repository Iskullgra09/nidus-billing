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
