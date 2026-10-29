from typing import Any, Dict, Tuple

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fiscal_profile_upsert_and_get(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client
    payload = {
        "legal_name": "Acme Costa Rica SA",
        "trade_name": "Acme",
        "identification_type": "juridica",
        "identification_number": "3101123456",
        "economic_activity_code": "620100",
        "branch_code": "001",
        "province": "San José",
        "canton": "Central",
        "district": "Carmen",
        "country_code": "CR",
    }
    put_res = await client.put("/api/v1/billing/fiscal-profile", json=payload)
    assert put_res.status_code == 200, put_res.text
    body = put_res.json()["data"]
    assert body["legal_name"] == "Acme Costa Rica SA"
    assert body["identification_type"] == "juridica"

    get_res = await client.get("/api/v1/billing/fiscal-profile")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["identification_number"] == "3101123456"


@pytest.mark.asyncio
async def test_hacienda_credentials_status_without_secrets(
    auth_client: Tuple[AsyncClient, Dict[str, Any]],
) -> None:
    client, _ = auth_client
    form = {
        "environment": "sandbox",
        "username": "mh-user@example.com",
        "p12_password": "secret-pass",
    }
    files = {"p12_file": ("cert.p12", b"fake-p12-bytes", "application/x-pkcs12")}
    put_res = await client.put(
        "/api/v1/billing/hacienda-credentials",
        data=form,
        files=files,
    )
    assert put_res.status_code == 200, put_res.text
    data = put_res.json()["data"]
    assert data["configured"] is True
    assert data["has_p12"] is True
    assert data["has_p12_password"] is True
    assert "p12_ciphertext" not in data
    assert "p12_password" not in data

    get_res = await client.get("/api/v1/billing/hacienda-credentials")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["username"] == "mh-user@example.com"
