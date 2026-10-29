from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

FE_NS = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica"


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
    emitter: XmlParty
    receptor: XmlParty
    lines: list[XmlLine]
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    payment_condition: str


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.00001'))}"


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
    issued = data.issued_at
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    _text(root, "FechaEmision", issued.isoformat(timespec="seconds"))

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
        _text(ubicacion, "OtrasSenas", data.emitter.other_signs or "N/D")
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
        if line.cabys_code:
            _text(linea, "CodigoCABYS", line.cabys_code)
        if line.sku:
            codigo = SubElement(linea, "CodigoComercial")
            _text(codigo, "Tipo", "04")
            _text(codigo, "Codigo", line.sku[:20])
        _text(linea, "Cantidad", _money(line.quantity))
        _text(linea, "UnidadMedida", (line.unit or "Unid")[:15])
        _text(linea, "Detalle", line.description[:200])
        _text(linea, "PrecioUnitario", _money(line.unit_price))
        _text(linea, "MontoTotal", _money(line.subtotal))
        _text(linea, "SubTotal", _money(line.subtotal))
        if line.tax_amount > 0 and line.tax_rate is not None:
            impuesto = SubElement(linea, "Impuesto")
            _text(impuesto, "Codigo", "01")
            _text(impuesto, "CodigoTarifaIVA", line.tax_code)
            _text(impuesto, "Tarifa", _money(line.tax_rate))
            _text(impuesto, "Monto", _money(line.tax_amount))
        _text(linea, "ImpuestoNeto", _money(line.tax_amount))
        _text(linea, "MontoTotalLinea", _money(line.total))

    resumen = SubElement(root, "ResumenFactura")
    codigo_tipo_cambio = SubElement(resumen, "CodigoTipoMoneda")
    _text(codigo_tipo_cambio, "CodigoMoneda", data.currency)
    _text(codigo_tipo_cambio, "TipoCambio", "1.00000" if data.currency == "CRC" else "1.00000")
    _text(resumen, "TotalVentaNeta", _money(data.subtotal))
    _text(resumen, "TotalImpuesto", _money(data.tax_total))
    _text(resumen, "TotalComprobante", _money(data.total))

    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")
