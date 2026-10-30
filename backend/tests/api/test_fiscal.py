from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from httpx import AsyncClient


def _test_p12(password: bytes = b"secret-pass") -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Nidus Test Signer")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2027, 1, 1, tzinfo=timezone.utc))
        .sign(key, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        name=b"nidus-test",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    )


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
        "province": "1",
        "canton": "01",
        "district": "01",
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
    password = "secret-pass"
    form = {
        "environment": "sandbox",
        "username": "mh-user@example.com",
        "p12_password": password,
    }
    files = {
        "p12_file": (
            "cert.p12",
            _test_p12(password.encode("utf-8")),
            "application/x-pkcs12",
        )
    }
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
