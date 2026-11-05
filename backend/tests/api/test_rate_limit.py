import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from app.core.config import settings
from app.core.rate_limit import clear_rate_limit_store


async def _issued_invoice(client: AsyncClient) -> str:
    customer = await client.post(
        "/api/v1/billing/customers",
        json={"name": "Rate Limit Co", "email": "rl@acme.example", "tax_id": "3101888001"},
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
                    "description": "RL line",
                    "quantity": "1",
                    "unit_price": "10",
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
    return invoice_id


async def _fiscal_profile(client: AsyncClient) -> None:
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


def _enable_strict(monkeypatch: MonkeyPatch, *, max_hits: int = 3) -> None:
    clear_rate_limit_store()
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_STRICT_MAX", max_hits)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)


@pytest.mark.asyncio
async def test_forgot_password_rate_limited(
    async_client: AsyncClient, monkeypatch: MonkeyPatch
) -> None:
    _enable_strict(monkeypatch, max_hits=3)

    payload = {"email": "rate-limit@example.com"}
    for _ in range(3):
        ok = await async_client.post("/api/v1/auth/forgot-password", json=payload)
        assert ok.status_code == 200

    blocked = await async_client.post("/api/v1/auth/forgot-password", json=payload)
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["status"] == "error"
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert blocked.headers.get("retry-after") is not None


@pytest.mark.asyncio
async def test_invoice_send_email_rate_limited(
    auth_client: tuple[AsyncClient, dict],
    monkeypatch: MonkeyPatch,
) -> None:
    client, _ = auth_client
    invoice_id = await _issued_invoice(client)
    _enable_strict(monkeypatch, max_hits=3)

    for _ in range(3):
        ok = await client.post(f"/api/v1/billing/invoices/{invoice_id}/send-email", json={})
        assert ok.status_code == 201, ok.text

    blocked = await client.post(f"/api/v1/billing/invoices/{invoice_id}/send-email", json={})
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "RATE_LIMIT_EXCEEDED"
    assert blocked.headers.get("retry-after") is not None


@pytest.mark.asyncio
async def test_invoice_emit_hacienda_rate_limited(
    auth_client: tuple[AsyncClient, dict],
    monkeypatch: MonkeyPatch,
) -> None:
    client, _ = auth_client
    await _fiscal_profile(client)
    invoice_id = await _issued_invoice(client)
    _enable_strict(monkeypatch, max_hits=3)

    # First emit succeeds; subsequent calls still consume the bucket (409 conflict).
    statuses: list[int] = []
    for _ in range(3):
        res = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
        statuses.append(res.status_code)
        assert res.status_code in {200, 409}, res.text
    assert 200 in statuses

    blocked = await client.post(f"/api/v1/billing/invoices/{invoice_id}/emit-hacienda")
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_hacienda_credentials_rate_limited(
    auth_client: tuple[AsyncClient, dict],
    monkeypatch: MonkeyPatch,
) -> None:
    client, _ = auth_client
    _enable_strict(monkeypatch, max_hits=3)

    form = {
        "environment": "sandbox",
        "username": "user@atv.example",
        "pin": "pin-secret",
    }
    for _ in range(3):
        ok = await client.put("/api/v1/billing/hacienda-credentials", data=form)
        assert ok.status_code == 200, ok.text

    blocked = await client.put("/api/v1/billing/hacienda-credentials", data=form)
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "RATE_LIMIT_EXCEEDED"
