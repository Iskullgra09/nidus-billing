from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.models.billing.enums import HaciendaEnvironment, HaciendaFiscalStatus

SANDBOX_API = "https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1"
PROD_API = "https://api.comprobanteselectronicos.go.cr/recepcion/v1"
SANDBOX_IDP = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token"
PROD_IDP = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token"


@dataclass(frozen=True)
class HaciendaSubmitResult:
    status: HaciendaFiscalStatus
    raw_status: str
    message: str
    response_xml: str | None
    mock: bool


class HaciendaClient:
    def __init__(
        self,
        *,
        environment: HaciendaEnvironment,
        username: str,
        password: str,
        client_id: str,
        client_secret: str,
        live: bool,
    ) -> None:
        self.environment = environment
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.live = live
        self.api_base = PROD_API if environment == HaciendaEnvironment.PRODUCTION else SANDBOX_API
        self.idp_url = PROD_IDP if environment == HaciendaEnvironment.PRODUCTION else SANDBOX_IDP

    async def submit(
        self,
        *,
        clave: str,
        issued_at: datetime,
        emitter_type: str,
        emitter_number: str,
        receptor_type: Optional[str],
        receptor_number: Optional[str],
        xml_signed: str,
    ) -> HaciendaSubmitResult:
        if not self.live:
            return HaciendaSubmitResult(
                status=HaciendaFiscalStatus.SUBMITTED,
                raw_status="recibido",
                message="Mock Hacienda submit accepted for local/dev.",
                response_xml=None,
                mock=True,
            )

        token = await self._token()
        payload: dict[str, Any] = {
            "clave": clave,
            "fecha": issued_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "emisor": {
                "tipoIdentificacion": emitter_type,
                "numeroIdentificacion": emitter_number,
            },
            "comprobanteXml": base64.b64encode(xml_signed.encode("utf-8")).decode("ascii"),
        }
        if receptor_type and receptor_number:
            payload["receptor"] = {
                "tipoIdentificacion": receptor_type,
                "numeroIdentificacion": receptor_number,
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/recepcion",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code in {200, 201, 202}:
            return HaciendaSubmitResult(
                status=HaciendaFiscalStatus.SUBMITTED,
                raw_status="recibido",
                message="Submitted to Hacienda recepcion API.",
                response_xml=None,
                mock=False,
            )
        return HaciendaSubmitResult(
            status=HaciendaFiscalStatus.ERROR,
            raw_status=str(response.status_code),
            message=response.text[:2000],
            response_xml=None,
            mock=False,
        )

    async def verify(self, clave: str) -> HaciendaSubmitResult:
        if not self.live:
            return HaciendaSubmitResult(
                status=HaciendaFiscalStatus.ACCEPTED,
                raw_status="aceptado",
                message="Mock Hacienda verify: accepted.",
                response_xml=None,
                mock=True,
            )

        token = await self._token()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.api_base}/recepcion/{clave}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            return HaciendaSubmitResult(
                status=HaciendaFiscalStatus.ERROR,
                raw_status=str(response.status_code),
                message=response.text[:2000],
                response_xml=None,
                mock=False,
            )
        body = response.json()
        raw = str(body.get("ind-estado") or body.get("estado") or body.get("status") or "").lower()
        mapped = _map_mh_status(raw)
        return HaciendaSubmitResult(
            status=mapped,
            raw_status=raw or "unknown",
            message=str(body.get("respuesta-xml") or body.get("mensaje") or raw)[:2000],
            response_xml=body.get("respuesta-xml"),
            mock=False,
        )

    async def _token(self) -> str:
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.idp_url, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("Hacienda IdP did not return access_token")
        return token


def _map_mh_status(raw: str) -> HaciendaFiscalStatus:
    value = raw.lower()
    if "acept" in value:
        return HaciendaFiscalStatus.ACCEPTED
    if "rechaz" in value:
        return HaciendaFiscalStatus.REJECTED
    if "proces" in value or "recib" in value:
        return HaciendaFiscalStatus.PROCESSING
    if not value:
        return HaciendaFiscalStatus.PROCESSING
    return HaciendaFiscalStatus.ERROR
