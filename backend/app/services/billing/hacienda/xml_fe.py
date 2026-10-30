from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FE_NS = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica"
try:
    _CR_TZ = ZoneInfo("America/Costa_Rica")
except ZoneInfoNotFoundError:
    # Fallback when tzdata is missing (common on bare Windows Python).
    _CR_TZ = timezone(timedelta(hours=-6))


def format_fecha_emision_cr(issued_at: datetime, *, for_xml: bool = True) -> str:
    """Costa Rica local timestamp for FE.

    XML ``FechaEmision`` is ``xs:dateTime`` (offset with colon, e.g. ``-06:00``).
    Recepción JSON ``fecha`` uses the compact form Hacienda examples show (``-0600``).
    """
    local = issued_at
    if local.tzinfo is None:
        local = local.replace(tzinfo=timezone.utc)
    local = local.astimezone(_CR_TZ)
    offset = local.utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    suffix = f"{sign}{hours:02d}:{minutes:02d}" if for_xml else f"{sign}{hours:02d}{minutes:02d}"
    return f"{local.strftime('%Y-%m-%dT%H:%M:%S')}{suffix}"


@dataclass(frozen=True)
class XmlParty:
    identification_type_code: str
    identification_number: str
    name: str
    province: str | None = None
    canton: str | None = None
    district: str | None = None
    other_signs: str | None = None
    phone: str | None = None
    email: str | None = None
    economic_activity_code: str | None = None


@dataclass(frozen=True)
class XmlLine:
    number: int
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    tax_rate: Decimal | None
    tax_code: str
    cabys_code: str | None = None
    sku: str | None = None


@dataclass(frozen=True)
class FacturaElectronicaInput:
    clave: str
    consecutive: str
    issued_at: datetime
    currency: str
    exchange_rate: Decimal
    emitter: XmlParty
    receptor: XmlParty
    lines: list[XmlLine]
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    payment_condition: str


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.00001'))}"


def normalize_cabys_code(value: str | None) -> str | None:
    """Pad/trim CABYS to 13 digits for FE v4.4 XSD. Does not check the BCCR catalog."""
    if value is None:
        return None
    digits = "".join(ch for ch in value.strip() if ch.isdigit())
    if not digits:
        return None
    if len(digits) > 13:
        return digits[:13]
    return digits.ljust(13, "0")


_UNIDAD_ALIASES: dict[str, str] = {
    "unit": "Unid",
    "unidad": "Unid",
    "unid": "Unid",
    "units": "Unid",
    "hour": "h",
    "hora": "h",
    "hours": "h",
    "hr": "h",
    "hrs": "h",
    "min": "Min",
    "minuto": "Min",
    "minutes": "Min",
    "month": "Spe",
    "mes": "Spe",
    "service": "Spe",
    "servicio": "Spe",
    "services": "Spe",
    "other": "Otros",
    "otros": "Otros",
    "os": "Os",
    "spe": "Spe",
}


def normalize_unidad_medida(value: str | None) -> str:
    """Map catalog/UI units onto MH UnidadMedida codes (unknown → Unid)."""
    raw = (value or "").strip()
    if not raw:
        return "Unid"
    if raw in {
        "1",
        "Unid",
        "Spe",
        "Os",
        "Otros",
        "h",
        "Min",
        "mL",
        "Kg",
        "km",
        "Km",
        "m",
        "m²",
        "m³",
        "L",
        "Sp",
    }:
        return raw[:15]
    mapped = _UNIDAD_ALIASES.get(raw.lower())
    if mapped:
        return mapped
    return "Unid"


def _text(parent: Element, tag: str, value: str | None) -> None:
    if value is None or value == "":
        return
    node = SubElement(parent, tag)
    node.text = value


def build_factura_electronica_xml(data: FacturaElectronicaInput) -> str:
    root = Element("FacturaElectronica", xmlns=FE_NS)
    _text(root, "Clave", data.clave)
    _text(root, "ProveedorSistemas", "Nidus Billing")
    if data.emitter.economic_activity_code:
        _text(root, "CodigoActividadEmisor", data.emitter.economic_activity_code[:6].ljust(6, "0")[:6])
    _text(root, "NumeroConsecutivo", data.consecutive)
    _text(root, "FechaEmision", format_fecha_emision_cr(data.issued_at))

    emisor = SubElement(root, "Emisor")
    nombre = SubElement(emisor, "Nombre")
    nombre.text = data.emitter.name
    ident = SubElement(emisor, "Identificacion")
    _text(ident, "Tipo", data.emitter.identification_type_code)
    _text(ident, "Numero", data.emitter.identification_number)
    if data.emitter.province or data.emitter.canton or data.emitter.district:
        ubicacion = SubElement(emisor, "Ubicacion")
        _text(ubicacion, "Provincia", data.emitter.province or "1")
        _text(ubicacion, "Canton", data.emitter.canton or "01")
        _text(ubicacion, "Distrito", data.emitter.district or "01")
        # FE XSD requires OtrasSenas minLength 5.
        otras = (data.emitter.other_signs or "").strip() or "Costa Rica"
        if len(otras) < 5:
            otras = f"{otras} — CR".strip(" —")
        _text(ubicacion, "OtrasSenas", otras[:250])
    if data.emitter.email:
        _text(emisor, "CorreoElectronico", data.emitter.email)

    receptor = SubElement(root, "Receptor")
    _text(receptor, "Nombre", data.receptor.name)
    r_ident = SubElement(receptor, "Identificacion")
    _text(r_ident, "Tipo", data.receptor.identification_type_code)
    _text(r_ident, "Numero", data.receptor.identification_number)
    if data.receptor.email:
        _text(receptor, "CorreoElectronico", data.receptor.email)

    condicion = "01" if data.payment_condition == "contado" else "02"
    _text(root, "CondicionVenta", condicion)

    detalle = SubElement(root, "DetalleServicio")
    for line in data.lines:
        linea = SubElement(detalle, "LineaDetalle")
        _text(linea, "NumeroLinea", str(line.number))
        cabys = normalize_cabys_code(line.cabys_code)
        if cabys:
            _text(linea, "CodigoCABYS", cabys)
        if line.sku:
            codigo = SubElement(linea, "CodigoComercial")
            _text(codigo, "Tipo", "04")
            _text(codigo, "Codigo", line.sku[:20])
        _text(linea, "Cantidad", _money(line.quantity))
        _text(linea, "UnidadMedida", normalize_unidad_medida(line.unit))
        _text(linea, "Detalle", line.description[:200])
        _text(linea, "PrecioUnitario", _money(line.unit_price))
        _text(linea, "MontoTotal", _money(line.subtotal))
        _text(linea, "SubTotal", _money(line.subtotal))
        # FE v4.4 LineaDetalle: BaseImponible must precede Impuesto when the line is taxed.
        if line.tax_amount > 0 and line.tax_rate is not None:
            _text(linea, "BaseImponible", _money(line.subtotal))
            impuesto = SubElement(linea, "Impuesto")
            _text(impuesto, "Codigo", "01")
            _text(impuesto, "CodigoTarifaIVA", line.tax_code)
            _text(impuesto, "Tarifa", _money(line.tax_rate))
            _text(impuesto, "Monto", _money(line.tax_amount))
            _text(linea, "ImpuestoAsumidoEmisorFabrica", _money(Decimal("0")))
        _text(linea, "ImpuestoNeto", _money(line.tax_amount))
        _text(linea, "MontoTotalLinea", _money(line.total))

    _append_resumen_factura(root, data)

    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def _is_service_cabys(cabys: str | None) -> bool:
    """MH anexos: CABYS leading digit 5–9 = servicio; 0–4 = mercancía."""
    digits = normalize_cabys_code(cabys) or ""
    return bool(digits) and digits[0] in "56789"


def _append_resumen_factura(root: Element, data: FacturaElectronicaInput) -> None:
    """ResumenFactura in FE v4.4 particle order (TotalVenta before TotalVentaNeta, etc.)."""
    resumen = SubElement(root, "ResumenFactura")
    codigo_tipo_cambio = SubElement(resumen, "CodigoTipoMoneda")
    _text(codigo_tipo_cambio, "CodigoMoneda", data.currency)
    rate = data.exchange_rate if data.currency != "CRC" else Decimal("1")
    _text(codigo_tipo_cambio, "TipoCambio", _money(rate))

    total_serv_gravados = Decimal("0")
    total_merc_gravadas = Decimal("0")
    tax_by_code: dict[tuple[str, str], Decimal] = {}
    for line in data.lines:
        if line.tax_amount > 0:
            if _is_service_cabys(line.cabys_code):
                total_serv_gravados += line.subtotal
            else:
                total_merc_gravadas += line.subtotal
            key = ("01", line.tax_code or "08")
            tax_by_code[key] = tax_by_code.get(key, Decimal("0")) + line.tax_amount

    total_gravado = total_serv_gravados + total_merc_gravadas
    total_exento = data.subtotal - total_gravado
    if total_exento < 0:
        total_exento = Decimal("0")

    if total_serv_gravados > 0:
        _text(resumen, "TotalServGravados", _money(total_serv_gravados))
    if total_merc_gravadas > 0:
        _text(resumen, "TotalMercanciasGravadas", _money(total_merc_gravadas))
    if total_gravado > 0:
        _text(resumen, "TotalGravado", _money(total_gravado))
    if total_exento > 0:
        _text(resumen, "TotalExento", _money(total_exento))

    total_venta = total_gravado + total_exento
    _text(resumen, "TotalVenta", _money(total_venta))
    _text(resumen, "TotalVentaNeta", _money(total_venta))

    for (codigo, tarifa), monto in sorted(tax_by_code.items()):
        desglose = SubElement(resumen, "TotalDesgloseImpuesto")
        _text(desglose, "Codigo", codigo)
        _text(desglose, "CodigoTarifaIVA", tarifa)
        _text(desglose, "TotalMontoImpuesto", _money(monto))

    if data.tax_total > 0:
        _text(resumen, "TotalImpuesto", _money(data.tax_total))

    # MedioPago is required for contado; crédito (02/08/10) may omit it.
    if data.payment_condition == "contado":
        medio = SubElement(resumen, "MedioPago")
        _text(medio, "TipoMedioPago", "01")
        _text(medio, "TotalMedioPago", _money(data.total))

    _text(resumen, "TotalComprobante", _money(data.total))
