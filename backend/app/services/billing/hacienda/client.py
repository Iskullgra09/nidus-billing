from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx

from app.models.billing.enums import HaciendaEnvironment, HaciendaFiscalStatus

from .mh_message import humanize_mh_message

# Legacy host path (.../recepcion-sandbox/v1) returns API Gateway 403 for valid tokens.
SANDBOX_API = "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1"
PROD_API = "https://api.comprobanteselectronicos.go.cr/recepcion/v1"
SANDBOX_IDP = (
    "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag"
    "/protocol/openid-connect/token"
)
PROD_IDP = (
    "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut"
    "/protocol/openid-connect/token"
)


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

        token, token_type = await self._token()
        payload: dict[str, Any] = {
            "clave": clave,
            "fecha": _format_mh_fecha(issued_at),
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

        auth_scheme = (token_type or "bearer").strip() or "bearer"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/recepcion",
                json=payload,
                headers={
                    "Authorization": f"{auth_scheme} {token}",
                    "Content-Type": "application/json",
                },
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

    async def submit_mensaje_receptor(
        self,
        *,
        clave: str,
        issued_at: datetime,
        emitter_type: str,
        emitter_number: str,
        receptor_type: str,
        receptor_number: str,
        xml_signed: str,
    ) -> HaciendaSubmitResult:
        return await self.submit(
            clave=clave,
            issued_at=issued_at,
            emitter_type=emitter_type,
            emitter_number=emitter_number,
            receptor_type=receptor_type,
            receptor_number=receptor_number,
            xml_signed=xml_signed,
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

        token, token_type = await self._token()
        auth_scheme = (token_type or "bearer").strip() or "bearer"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.api_base}/recepcion/{clave}",
                headers={"Authorization": f"{auth_scheme} {token}"},
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
        response_xml = body.get("respuesta-xml")
        opaque = response_xml or body.get("mensaje") or raw
        message = humanize_mh_message(str(opaque) if opaque is not None else None) or (
            raw or "unknown"
        )
        return HaciendaSubmitResult(
            status=mapped,
            raw_status=raw or "unknown",
            message=message[:2000],
            response_xml=response_xml if isinstance(response_xml, str) else None,
            mock=False,
        )

    async def _token(self) -> tuple[str, str]:
        data: dict[str, str] = {
            "grant_type": "password",
            "client_id": self.client_id or "api-stag",
            "username": self.username,
            "password": self.password,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.idp_url, data=data)
        if response.status_code >= 400:
            detail = (response.text or "")[:300]
            raise RuntimeError(
                f"Hacienda IdP auth failed ({response.status_code}): {detail}"
            )
        body = response.json()
        token = body.get("access_token")
        if not token:
            raise RuntimeError("Hacienda IdP did not return access_token")
        token_type = str(body.get("token_type") or "bearer")
        return str(token), token_type


def _format_mh_fecha(issued_at: datetime) -> str:
    """MH recepción JSON fecha uses compact CR offset, e.g. 2016-01-01T00:00:00-0600."""
    from .xml_fe import format_fecha_emision_cr

    return format_fecha_emision_cr(issued_at, for_xml=False)


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
