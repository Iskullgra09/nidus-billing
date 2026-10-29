from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class ParsedInboundDocument:
    clave: str
    consecutive: str | None
    document_type: str
    issued_at: datetime | None
    currency: str
    exchange_rate: Decimal | None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    emitter_identification_type: str | None
    emitter_identification_number: str | None
    emitter_name: str | None
    emitter_email: str | None
    receptor_identification_number: str | None


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _find_text(root: ET.Element, *path: str) -> str | None:
    node: ET.Element | None = root
    for name in path:
        if node is None:
            return None
        next_node = None
        for child in node:
            if _local(child.tag) == name:
                next_node = child
                break
        node = next_node
    if node is None or node.text is None:
        return None
    text = node.text.strip()
    return text or None


def _decimal(raw: str | None, default: str = "0") -> Decimal:
    try:
        return Decimal(raw or default)
    except (InvalidOperation, TypeError):
        return Decimal(default)


def _guess_document_type(root: ET.Element) -> str:
    local = _local(root.tag).lower()
    if "nota" in local and "debito" in local:
        return "02"
    if "nota" in local and "credito" in local:
        return "03"
    if "tiquete" in local:
        return "04"
    return "01"


def parse_inbound_factura_xml(xml: str) -> ParsedInboundDocument:
    root = ET.fromstring(xml)
    clave = _find_text(root, "Clave")
    if not clave or len("".join(ch for ch in clave if ch.isdigit())) != 50:
        raise ValueError("Inbound XML missing a valid 50-digit Clave")
    clave_digits = "".join(ch for ch in clave if ch.isdigit())

    issued_raw = _find_text(root, "FechaEmision")
    issued_at = None
    if issued_raw:
        try:
            issued_at = datetime.fromisoformat(issued_raw.replace("Z", "+00:00"))
        except ValueError:
            issued_at = None

    currency = _find_text(root, "ResumenFactura", "CodigoTipoMoneda", "CodigoMoneda") or "CRC"
    if currency not in {"CRC", "USD"}:
        currency = "CRC"
    rate_raw = _find_text(root, "ResumenFactura", "CodigoTipoMoneda", "TipoCambio")
    exchange_rate = _decimal(rate_raw) if currency == "USD" and rate_raw else None

    return ParsedInboundDocument(
        clave=clave_digits,
        consecutive=_find_text(root, "NumeroConsecutivo"),
        document_type=_guess_document_type(root),
        issued_at=issued_at,
        currency=currency,
        exchange_rate=exchange_rate,
        subtotal=_decimal(_find_text(root, "ResumenFactura", "TotalVentaNeta")),
        tax_total=_decimal(_find_text(root, "ResumenFactura", "TotalImpuesto")),
        total=_decimal(_find_text(root, "ResumenFactura", "TotalComprobante")),
        emitter_identification_type=_find_text(root, "Emisor", "Identificacion", "Tipo"),
        emitter_identification_number=_find_text(root, "Emisor", "Identificacion", "Numero"),
        emitter_name=_find_text(root, "Emisor", "Nombre"),
        emitter_email=_find_text(root, "Emisor", "CorreoElectronico"),
        receptor_identification_number=_find_text(root, "Receptor", "Identificacion", "Numero"),
    )
