from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from app.models.billing.enums import MensajeReceptorCode

MENSAJE_NS = (
    "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeReceptor"
)


@dataclass(frozen=True)
class MensajeReceptorInput:
    clave: str
    emitter_number: str
    receptor_number: str
    consecutive_receptor: str
    issued_at: datetime
    mensaje: MensajeReceptorCode
    detalle: str | None
    tax_total: Decimal
    total: Decimal


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.00001'))}"


def _text(parent: Element, tag: str, value: str) -> None:
    node = SubElement(parent, tag)
    node.text = value


def build_mensaje_receptor_xml(data: MensajeReceptorInput) -> str:
    root = Element("MensajeReceptor", xmlns=MENSAJE_NS)
    _text(root, "Clave", data.clave)
    _text(root, "NumeroCedulaEmisor", data.emitter_number)
    issued = data.issued_at
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    _text(root, "FechaEmisionDoc", issued.isoformat(timespec="seconds"))
    _text(root, "Mensaje", data.mensaje.value)
    if data.detalle:
        _text(root, "DetalleMensaje", data.detalle[:80])
    _text(root, "MontoTotalImpuesto", _money(data.tax_total))
    _text(root, "TotalFactura", _money(data.total))
    _text(root, "NumeroCedulaReceptor", data.receptor_number)
    _text(root, "NumeroConsecutivoReceptor", data.consecutive_receptor)
    return tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
