"""Local FE v4.4 XSD gate before Hacienda recepción (structure only, not RUT/CABYS catalogs)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"
_FE_XSD = _SCHEMAS_DIR / "FacturaElectronica_V4.4.xsd"
_DS_NS = "http://www.w3.org/2000/09/xmldsig#"
_FE_NS = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica"


class FeXmlSchemaError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors) if errors else "FE XML failed XSD validation")


@lru_cache(maxsize=1)
def _fe_schema() -> etree.XMLSchema:
    if not _FE_XSD.is_file():
        raise FileNotFoundError(f"Missing vendored FE XSD: {_FE_XSD}")
    return etree.XMLSchema(etree.parse(str(_FE_XSD)))


def validate_factura_electronica_xml(
    xml: str | bytes,
    *,
    allow_missing_signature: bool = False,
) -> None:
    """Validate against vendored FacturaElectronica_V4.4.xsd.

    The official schema requires ``ds:Signature`` last. For unsigned drafts,
    ``allow_missing_signature=True`` validates a copy with a minimal Signature stub
    so we catch structure errors before signing. Emit should also validate the
    real signed XML with the default ``False``.
    """
    raw = xml.encode("utf-8") if isinstance(xml, str) else xml
    try:
        doc = etree.fromstring(raw)
    except etree.XMLSyntaxError as exc:
        raise FeXmlSchemaError([f"XML mal formado: {exc}"]) from exc

    if allow_missing_signature and not _has_signature(doc):
        doc = etree.fromstring(raw)
        doc.append(_signature_stub())

    schema = _fe_schema()
    if schema.validate(doc):
        return

    messages: list[str] = []
    for entry in schema.error_log:
        msg = (entry.message or "").strip()
        if allow_missing_signature and "Signature" in msg and "Missing child" in msg:
            continue
        if msg and msg not in messages:
            messages.append(_shorten_schema_message(msg))
        if len(messages) >= 5:
            break
    if not messages:
        return
    raise FeXmlSchemaError(messages)


def _has_signature(doc: etree._Element) -> bool:
    for child in doc:
        if isinstance(child.tag, str) and etree.QName(child).localname == "Signature":
            return True
    return False


def _signature_stub() -> etree._Element:
    """Minimal ds:Signature particle for unsigned XSD checks (not a real seal)."""
    sig = etree.Element(f"{{{_DS_NS}}}Signature")
    signed_info = etree.SubElement(sig, f"{{{_DS_NS}}}SignedInfo")
    etree.SubElement(
        signed_info,
        f"{{{_DS_NS}}}CanonicalizationMethod",
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    etree.SubElement(
        signed_info,
        f"{{{_DS_NS}}}SignatureMethod",
        Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    )
    reference = etree.SubElement(signed_info, f"{{{_DS_NS}}}Reference", URI="")
    etree.SubElement(
        reference,
        f"{{{_DS_NS}}}DigestMethod",
        Algorithm="http://www.w3.org/2001/04/xmlenc#sha256",
    )
    digest = etree.SubElement(reference, f"{{{_DS_NS}}}DigestValue")
    digest.text = "AA=="
    value = etree.SubElement(sig, f"{{{_DS_NS}}}SignatureValue")
    value.text = "AA=="
    return sig


def _shorten_schema_message(message: str) -> str:
    compact = message.replace(" ", "").lower()
    lower = message.lower()
    if "unidadmedida" in compact or ("enumeration" in lower and "'unit'" in lower):
        return (
            "UnidadMedida inválida para el XSD FE v4.4 "
            "(usa códigos MH: Unid, h, Spe, Os, …)."
        )
    if "codigocabys" in compact:
        return "CodigoCABYS no cumple el XSD FE v4.4 (13 dígitos)."
    if "totalventaneta" in compact and "totalventa" in compact:
        return "Orden inválido en ResumenFactura (falta TotalVenta antes de TotalVentaNeta)."
    if "impuesto" in lower and ("baseimponible" in compact or "one of" in lower):
        return "Orden inválido en LineaDetalle (BaseImponible debe ir antes de Impuesto)."
    if "fechaemision" in compact and "datetime" in lower:
        return "FechaEmision inválida (usa hora CR con offset -06:00)."
    if "otrassenas" in compact and "minlength" in lower:
        return "OtrasSenas del emisor debe tener al menos 5 caracteres."
    if "enumeration" in lower:
        head = message.split(".", 1)[0].strip()
        return head[:180] + ("…" if len(head) > 180 else "")
    cleaned = message.replace(f"{{{_FE_NS}}}", "").replace(f"{{{_DS_NS}}}", "ds:")
    if len(cleaned) > 220:
        return cleaned[:219].rstrip() + "…"
    return cleaned
