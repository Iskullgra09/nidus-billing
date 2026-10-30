from __future__ import annotations

import base64
import html
import re

from lxml import etree

_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")
_BRACKET_ERRORS_RE = re.compile(r"\[\s*(.*?)\s*\]", re.DOTALL)
_SANDBOX_NOISE_RE = re.compile(
    r"Este comprobante fue recibido en el ambiente de pruebas[^.]*\.\s*",
    re.IGNORECASE,
)
_ERRORS_INTRO_RE = re.compile(
    r"El comprobante electr[oó]nico tiene los siguientes errores:\s*",
    re.IGNORECASE,
)
_CABYS_LEN_RE = re.compile(
    r"Value\s+'([^']+)'\s+with length\s+=\s+'(\d+)'.*?minLength\s+'(\d+)'.*?CodigoCABYS",
    re.IGNORECASE | re.DOTALL,
)
_ENUM_VALUE_RE = re.compile(
    r"cvc-enumeration-valid:\s*Value\s+'([^']+)'\s+is not facet-valid",
    re.IGNORECASE,
)


def humanize_mh_message(raw: str | None, *, max_len: int = 500) -> str | None:
    """Extract a short operator-facing line from MH respuesta-xml / DetalleMensaje."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None

    xml_text = _maybe_decode_xml(text)
    if xml_text:
        detalle = _first_tag_text(xml_text, "DetalleMensaje")
        if detalle:
            return _summarize_detalle(detalle, max_len)
        mensaje = _first_tag_text(xml_text, "Mensaje")
        if mensaje and not (len(mensaje) <= 8 and mensaje.isdigit()):
            return _clean(mensaje, max_len)

    if _looks_like_opaque_blob(text):
        return None
    return _summarize_detalle(text, max_len)


def _summarize_detalle(detalle: str, max_len: int) -> str | None:
    cleaned = _clean(detalle, max_len=10_000)
    if not cleaned:
        return None

    cabys = _CABYS_LEN_RE.search(cleaned)
    if cabys:
        return _clean(
            f"CodigoCABYS '{cabys.group(1)}' tiene {cabys.group(2)} dígitos; "
            f"Hacienda exige {cabys.group(3)}.",
            max_len,
        )

    enum_msg = _friendly_enumeration(cleaned)
    if enum_msg:
        return _clean(enum_msg, max_len)

    complex_msg = _friendly_complex_order(cleaned)
    if complex_msg:
        return _clean(complex_msg, max_len)

    bracket = _BRACKET_ERRORS_RE.search(cleaned)
    if bracket:
        body = bracket.group(1)
        lines = [
            line.strip().strip(",")
            for line in re.split(r"[\n\r]+", body)
            if line.strip() and not line.lower().startswith("codigo,")
        ]
        friendly = [_friendly_xsd_line(line) for line in lines]
        friendly = [line for line in friendly if line]
        if friendly:
            return _clean("\n".join(friendly), max_len)

    without_noise = _SANDBOX_NOISE_RE.sub("", cleaned)
    without_noise = _ERRORS_INTRO_RE.sub("", without_noise).strip(" \n:-")
    return _clean(without_noise or cleaned, max_len)


def _friendly_enumeration(text: str) -> str | None:
    match = _ENUM_VALUE_RE.search(text)
    if not match:
        return None
    bad = match.group(1)
    lower = text.lower()
    if "unidadmedida" in lower or bad.lower() in {
        "unit",
        "hour",
        "month",
        "unidad",
        "hora",
        "mes",
    }:
        return (
            f"UnidadMedida '{bad}' no es válida para Hacienda. "
            "Usa códigos oficiales (ej. Unid, h, Spe, Os)."
        )
    return f"Valor '{bad}' no está en el catálogo permitido por Hacienda."


_COMPLEX_ORDER_RE = re.compile(
    r"cvc-complex-type\.2\.4\.a:.*?element\s+'[^']*:?([^'{}\"]+)'.*?One of\s+'[^']*:?([^'{}\",]+)",
    re.IGNORECASE | re.DOTALL,
)


def _friendly_complex_order(text: str) -> str | None:
    if "cvc-complex-type.2.4.a" not in text.lower():
        return None

    if re.search(r"TotalVentaNeta", text) and re.search(r"TotalVenta[}\"'\s,]", text):
        return (
            "Orden XML inválido en ResumenFactura: falta TotalVenta "
            "(y desgloses) antes de TotalVentaNeta (FE v4.4)."
        )
    if re.search(r":Impuesto}", text) or (
        "Impuesto" in text and ("BaseImponible" in text or "IVACobradoFabrica" in text)
    ):
        return (
            "Orden XML inválido en LineaDetalle: Impuesto fuera de secuencia "
            "(FE v4.4 espera BaseImponible antes de Impuesto)."
        )

    match = _COMPLEX_ORDER_RE.search(text)
    if match:
        found, expected = match.group(1), match.group(2)
        return (
            f"Orden XML inválido: apareció '{found}' donde se esperaba "
            f"'{expected}' (u otro nodo previo del esquema)."
        )
    return "Estructura XML inválida para el esquema de Hacienda (orden de nodos)."


_MH_QUOTED_MSG_RE = re.compile(r'""([^"]{12,})""')


def _friendly_xsd_line(line: str) -> str | None:
    cabys = _CABYS_LEN_RE.search(line)
    if cabys:
        return (
            f"CodigoCABYS '{cabys.group(1)}' tiene {cabys.group(2)} dígitos; "
            f"Hacienda exige {cabys.group(3)}."
        )
    enum_msg = _friendly_enumeration(line)
    if enum_msg:
        return enum_msg
    complex_msg = _friendly_complex_order(line)
    if complex_msg:
        return complex_msg
    quoted = _MH_QUOTED_MSG_RE.search(line)
    if quoted:
        return quoted.group(1).strip()
    cleaned = re.sub(r'^-?\d+,\s*""?', "", line).strip().strip('"')
    if not cleaned or cleaned.lower().startswith("codigo,"):
        return None
    if cleaned.lower().startswith("cvc-"):
        short = cleaned.split(". It must be", 1)[0]
        short = short.split("with respect to enumeration", 1)[0].rstrip(" ,")
        return short
    return cleaned


def _maybe_decode_xml(text: str) -> str | None:
    if text.lstrip().startswith("<"):
        return text
    compact = "".join(text.split())
    if len(compact) < 32 or not _BASE64_RE.match(compact):
        return None
    try:
        decoded = base64.b64decode(compact, validate=False)
    except Exception:
        return None
    if not decoded.lstrip().startswith(b"<?xml") and not decoded.lstrip().startswith(b"<"):
        return None
    return decoded.decode("utf-8", errors="replace")


def _first_tag_text(xml_text: str, tag: str) -> str | None:
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError:
        match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    for node in root.iter():
        local = etree.QName(node).localname if isinstance(node.tag, str) else ""
        if local == tag and node.text and node.text.strip():
            return node.text.strip()
    return None


def _looks_like_opaque_blob(text: str) -> bool:
    compact = "".join(text.split())
    if compact.startswith("eyJ") and compact.count(".") >= 2:
        return True
    if len(compact) > 120 and _BASE64_RE.match(compact) and "<" not in text:
        return True
    return False


def _clean(value: str, max_len: int) -> str:
    cleaned = html.unescape(value)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if len(cleaned) > max_len:
        return cleaned[: max_len - 1].rstrip() + "…"
    return cleaned
