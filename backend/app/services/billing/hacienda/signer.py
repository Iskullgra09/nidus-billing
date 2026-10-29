from __future__ import annotations

from dataclasses import dataclass

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree

from app.core.config import settings


@dataclass(frozen=True)
class SignResult:
    xml_signed: str
    mock: bool


def sign_factura_xml(
    xml_unsigned: str,
    *,
    p12_bytes: bytes | None,
    p12_password: str | None,
) -> SignResult:
    if not p12_bytes or p12_password is None:
        return _mock_sign(xml_unsigned)

    try:
        from signxml import DigestAlgorithm, methods
        from signxml.xades import XAdESSignaturePolicy, XAdESSigner
    except ImportError as exc:
        raise RuntimeError("signxml is required for live XAdES signing") from exc

    password = p12_password.encode("utf-8")
    key, cert, _additional = pkcs12.load_key_and_certificates(p12_bytes, password)
    if key is None or cert is None:
        raise ValueError("PKCS#12 did not contain a private key and certificate")

    root = etree.fromstring(xml_unsigned.encode("utf-8"))
    policy = XAdESSignaturePolicy(
        Identifier=settings.HACIENDA_XADES_POLICY_ID,
        Description=settings.HACIENDA_XADES_POLICY_DESCRIPTION,
        DigestMethod=DigestAlgorithm.SHA256,
        DigestValue=settings.HACIENDA_XADES_POLICY_DIGEST,
    )
    signer = XAdESSigner(
        method=methods.enveloped,
        signature_policy=policy,
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    signed_root = signer.sign(
        root,
        key=key,
        cert=cert.public_bytes(Encoding.PEM).decode("ascii"),
    )
    signed_xml = etree.tostring(
        signed_root,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")
    return SignResult(xml_signed=signed_xml, mock=False)


def _mock_sign(xml_unsigned: str) -> SignResult:
    marker = "<!-- nidus-mock-xades-epes -->"
    if marker in xml_unsigned:
        return SignResult(xml_signed=xml_unsigned, mock=True)
    if "</FacturaElectronica>" not in xml_unsigned:
        raise ValueError("Unsigned XML is missing FacturaElectronica root close tag")
    signed = xml_unsigned.replace(
        "</FacturaElectronica>",
        f"{marker}</FacturaElectronica>",
        1,
    )
    return SignResult(xml_signed=signed, mock=True)
