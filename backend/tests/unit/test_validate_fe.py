from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.services.billing.hacienda.validate_fe import (
    FeXmlSchemaError,
    validate_factura_electronica_xml,
)
from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
)


def _sample_xml(*, unit: str = "Unid", with_base: bool = True) -> str:
    tax = Decimal("13") if with_base else Decimal("0")
    rate = Decimal("13") if with_base else None
    return build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave="5" * 50,
            consecutive="00100001010000000001",
            issued_at=datetime(2026, 10, 30, 15, 0, tzinfo=timezone.utc),
            currency="CRC",
            exchange_rate=Decimal("1"),
            emitter=XmlParty(
                "01",
                "207510859",
                "Emisor",
                province="1",
                canton="01",
                district="01",
                other_signs="N/D",
                email="a@b.c",
                economic_activity_code="620100",
            ),
            receptor=XmlParty("02", "3101123456", "Receptor", email="r@b.c"),
            lines=[
                XmlLine(
                    number=1,
                    description="Service",
                    quantity=Decimal("1"),
                    unit=unit,
                    unit_price=Decimal("100"),
                    subtotal=Decimal("100"),
                    tax_amount=tax,
                    total=Decimal("113") if with_base else Decimal("100"),
                    tax_rate=rate,
                    tax_code="08",
                    cabys_code="8311990000000",
                    sku="SKU1",
                )
            ],
            subtotal=Decimal("100"),
            tax_total=tax,
            total=Decimal("113") if with_base else Decimal("100"),
            payment_condition="contado",
        )
    )


def test_valid_builder_xml_passes_xsd() -> None:
    validate_factura_electronica_xml(_sample_xml(), allow_missing_signature=True)


def test_invalid_unidad_medida_fails_xsd() -> None:
    bad = _sample_xml(unit="unit")
    # Builder normalizes unit→Unid; force a bad value into the XML string.
    bad = bad.replace("<UnidadMedida>Unid</UnidadMedida>", "<UnidadMedida>unit</UnidadMedida>")
    with pytest.raises(FeXmlSchemaError) as exc:
        validate_factura_electronica_xml(bad, allow_missing_signature=True)
    assert exc.value.errors
    assert any("UnidadMedida" in e or "unidad" in e.lower() for e in exc.value.errors)


def test_missing_total_venta_fails_xsd() -> None:
    xml = _sample_xml()
    broken = xml.replace("<TotalVenta>100.00000</TotalVenta>", "")
    with pytest.raises(FeXmlSchemaError):
        validate_factura_electronica_xml(broken, allow_missing_signature=True)


def test_unsigned_without_stub_flag_fails_for_missing_signature() -> None:
    with pytest.raises(FeXmlSchemaError) as exc:
        validate_factura_electronica_xml(_sample_xml(), allow_missing_signature=False)
    assert any("Signature" in e or "Missing" in e for e in exc.value.errors)
