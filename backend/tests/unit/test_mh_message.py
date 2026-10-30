import base64

from app.services.billing.hacienda.mh_message import humanize_mh_message


def test_humanize_detalle_keeps_only_error_lines() -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<MensajeHacienda>"
        "<Mensaje>3</Mensaje>"
        "<DetalleMensaje>"
        "Este comprobante fue recibido en el ambiente de pruebas, "
        "por lo cual no tiene validez para fines tributarios.\n\n"
        "El comprobante electrónico tiene los siguientes errores: \n"
        "[\n"
        "La firma del comprobante electrónico no es válida "
        "(El XML fue modificado luego de haber sido firmado).\n"
        "]"
        "</DetalleMensaje>"
        "</MensajeHacienda>"
    )
    blob = base64.b64encode(xml.encode("utf-8")).decode("ascii")
    assert humanize_mh_message(blob) == (
        "La firma del comprobante electrónico no es válida "
        "(El XML fue modificado luego de haber sido firmado)."
    )


def test_humanize_hides_opaque_jwt_like_blob() -> None:
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
    assert humanize_mh_message(token) is None


def test_humanize_keeps_plain_text() -> None:
    assert humanize_mh_message("Submitted to Hacienda recepcion API.") == (
        "Submitted to Hacienda recepcion API."
    )


def test_humanize_cabys_xsd_error() -> None:
    detalle = (
        "codigo, mensaje, fila, columna\n"
        "-1, \"\"cvc-minLength-valid: Value '85444200' with length = '8' "
        "is not facet-valid with respect to minLength '13' for type "
        "'#AnonType_CodigoCABYSLineaDetalleDetalleServicioFacturaElectronica'.\"\", "
        "2, 1076"
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<MensajeHacienda>"
        f"<DetalleMensaje>{detalle}</DetalleMensaje>"
        "</MensajeHacienda>"
    )
    blob = base64.b64encode(xml.encode("utf-8")).decode("ascii")
    assert humanize_mh_message(blob) == (
        "CodigoCABYS '85444200' tiene 8 dígitos; Hacienda exige 13."
    )


def test_humanize_total_venta_order_error() -> None:
    detalle = (
        "cvc-complex-type.2.4.a: Invalid content was found starting with element "
        "'{\"https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica\":TotalVentaNeta}'. "
        "One of '{...TotalGravado..., "
        '{"https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica":TotalVenta}\' '
        "is expected."
    )
    msg = humanize_mh_message(detalle)
    assert msg is not None
    assert "TotalVenta" in msg
    assert "TotalVentaNeta" in msg


def test_humanize_impuesto_order_error() -> None:
    detalle = (
        "cvc-complex-type.2.4.a: Invalid content was found starting with element "
        "'{\"https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica\":Impuesto}'. "
        "One of '{\"https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica\":IVACobradoFabrica,"
        '{"https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica":BaseImponible}\'.'
    )
    msg = humanize_mh_message(detalle)
    assert msg is not None
    assert "BaseImponible" in msg
    assert "Impuesto" in msg
    assert len(msg) < 200


def test_humanize_unidad_medida_enum_error() -> None:
    detalle = (
        "cvc-enumeration-valid: Value 'unit' is not facet-valid with respect to "
        "enumeration '[Al, Alc, Cm, Cm2, Cm3, Unid, Spe, Os, Otros, h, Min, …]'. "
        "It must be a value from the enumeration."
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<MensajeHacienda>"
        f"<DetalleMensaje>{detalle}</DetalleMensaje>"
        "</MensajeHacienda>"
    )
    blob = base64.b64encode(xml.encode("utf-8")).decode("ascii")
    msg = humanize_mh_message(blob)
    assert msg is not None
    assert "UnidadMedida 'unit'" in msg
    assert "Unid" in msg
    assert "enumeration '[" not in msg
    assert len(msg) < 200
