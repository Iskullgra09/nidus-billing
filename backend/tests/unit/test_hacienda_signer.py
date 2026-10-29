from datetime import datetime, timezone
from decimal import Decimal

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from app.services.billing.hacienda.signer import sign_factura_xml
from app.services.billing.hacienda.xml_fe import (
    FacturaElectronicaInput,
    XmlLine,
    XmlParty,
    build_factura_electronica_xml,
)


def _sample_xml(*, currency: str = "CRC", exchange_rate: Decimal = Decimal("1")) -> str:
    issued = datetime(2026, 10, 29, 15, 0, tzinfo=timezone.utc)
    return build_factura_electronica_xml(
        FacturaElectronicaInput(
            clave="5" * 50,
            consecutive="00100001010000000001",
            issued_at=issued,
            currency=currency,
            exchange_rate=exchange_rate,
            emitter=XmlParty(
                identification_type_code="02",
                identification_number="3101123456",
                name="Emitter SA",
                province="1",
                canton="01",
                district="01",
                email="emit@example.com",
                economic_activity_code="620100",
            ),
            receptor=XmlParty(
                identification_type_code="02",
                identification_number="3101987654",
                name="Receptor SA",
                email="recv@example.com",
            ),
            lines=[
                XmlLine(
                    number=1,
                    description="Service",
                    quantity=Decimal("1"),
                    unit="Unid",
                    unit_price=Decimal("10"),
                    subtotal=Decimal("10"),
                    tax_amount=Decimal("1.3"),
                    total=Decimal("11.3"),
                    tax_rate=Decimal("13"),
                    tax_code="08",
                    cabys_code="85171200",
                )
            ],
            subtotal=Decimal("10"),
            tax_total=Decimal("1.3"),
            total=Decimal("11.3"),
            payment_condition="contado",
        )
    )


def _test_p12(password: bytes = b"test-pin") -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Nidus Test Signer")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2027, 1, 1, tzinfo=timezone.utc))
        .sign(key, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        name=b"nidus-test",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    )


def test_mock_sign_inserts_marker() -> None:
    xml = _sample_xml()
    result = sign_factura_xml(xml, p12_bytes=None, p12_password=None)
    assert result.mock is True
    assert "nidus-mock-xades-epes" in result.xml_signed


def test_xades_sign_with_p12() -> None:
    xml = _sample_xml()
    password = "test-pin"
    result = sign_factura_xml(
        xml,
        p12_bytes=_test_p12(password.encode("utf-8")),
        p12_password=password,
    )
    assert result.mock is False
    assert "Signature" in result.xml_signed
    assert "nidus-mock-xades-epes" not in result.xml_signed


def test_xml_includes_cabys_and_usd_tipo_cambio() -> None:
    xml = _sample_xml(currency="USD", exchange_rate=Decimal("520.00000"))
    assert "<CodigoCABYS>85171200</CodigoCABYS>" in xml
    assert "<CodigoMoneda>USD</CodigoMoneda>" in xml
    assert "<TipoCambio>520.00000</TipoCambio>" in xml
