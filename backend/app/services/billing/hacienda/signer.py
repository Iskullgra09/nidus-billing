from __future__ import annotations

from dataclasses import dataclass


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
        marker = "<!-- nidus-mock-xades-epes -->"
        if marker in xml_unsigned:
            return SignResult(xml_signed=xml_unsigned, mock=True)
        signed = xml_unsigned.replace(
            "</FacturaElectronica>",
            f"{marker}</FacturaElectronica>",
            1,
        )
        return SignResult(xml_signed=signed, mock=True)

    raise NotImplementedError(
        "Live XAdES-EPES signing with .p12 is not enabled in this slice; "
        "store credentials and use mock emit until the signer lands."
    )
