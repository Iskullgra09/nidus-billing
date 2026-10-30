from datetime import datetime, timezone
from decimal import Decimal

from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
    format_fecha_emision_cr,
    normalize_cabys_code,
    normalize_canton,
    normalize_distrito,
    normalize_provincia,
    normalize_unidad_medida,
)


def test_format_fecha_emision_uses_cr_offset() -> None:
    xml_stamp = format_fecha_emision_cr(datetime(2026, 10, 30, 2, 0, tzinfo=timezone.utc))
    assert xml_stamp.endswith("-06:00")
    assert xml_stamp.startswith("2026-10-29T20:00:00")
    api_stamp = format_fecha_emision_cr(
        datetime(2026, 10, 30, 2, 0, tzinfo=timezone.utc), for_xml=False
    )
    assert api_stamp.endswith("-0600")


def test_normalize_cabys_pads_to_13() -> None:
    assert normalize_cabys_code("85444200") == "8544420000000"
    assert normalize_cabys_code("8311990000000") == "8311990000000"


def test_normalize_ubicacion_codes_and_aliases() -> None:
    assert normalize_provincia("1") == "1"
    assert normalize_provincia("San José") == "1"
    assert normalize_canton("1", "1") == "01"
    assert normalize_canton("Central", "1") == "01"
    assert normalize_distrito("Carmen", "1", "01") == "01"
    assert normalize_distrito("01", "1", "01") == "01"


def test_normalize_unidad_medida_aliases() -> None:
    assert normalize_unidad_medida("unit") == "Unid"
    assert normalize_unidad_medida("hour") == "h"
    assert normalize_unidad_medida("month") == "Spe"
    assert normalize_unidad_medida("Unid") == "Unid"
    assert normalize_unidad_medida(None) == "Unid"
    assert normalize_unidad_medida("weird-free-text") == "Unid"


def test_line_includes_base_imponible_before_impuesto() -> None:
    xml = build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave="1" * 50,
            consecutive="00100001010000000001",
            issued_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
            currency="CRC",
            exchange_rate=Decimal("1"),
            emitter=XmlParty("01", "207510859", "Emisor"),
            receptor=XmlParty("02", "3101123456", "Receptor"),
            lines=[
                XmlLine(
                    number=1,
                    description="Service",
                    quantity=Decimal("1"),
                    unit="Unid",
                    unit_price=Decimal("100"),
                    subtotal=Decimal("100"),
                    tax_amount=Decimal("13"),
                    total=Decimal("113"),
                    tax_rate=Decimal("13"),
                    tax_code="08",
                    cabys_code="8311990000000",
                )
            ],
            subtotal=Decimal("100"),
            tax_total=Decimal("13"),
            total=Decimal("113"),
            payment_condition="contado",
        )
    )
    assert "<BaseImponible>100.00000</BaseImponible>" in xml
    assert xml.index("BaseImponible") < xml.index("<Impuesto>")
    assert "<ImpuestoAsumidoEmisorFabrica>0.00000</ImpuestoAsumidoEmisorFabrica>" in xml
    assert "<TotalVenta>100.00000</TotalVenta>" in xml
    assert xml.index("TotalVenta>") < xml.index("TotalVentaNeta>")
    assert "<TotalDesgloseImpuesto>" in xml
    assert "<MedioPago>" in xml
    assert "<TipoMedioPago>01</TipoMedioPago>" in xml
