from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass

from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from lxml.etree import SubElement

from app.core.config import settings


@dataclass(frozen=True)
class SignResult:
    xml_signed: str
    mock: bool


def load_pkcs12_key_and_cert(
    p12_bytes: bytes,
    p12_password: str | None,
) -> tuple[object, object]:
    if not p12_bytes:
        raise ValueError("PKCS#12 file is empty")

    candidates: list[bytes | None] = []
    seen: set[bytes | None] = set()

    def _add(value: bytes | None) -> None:
        if value in seen:
            return
        seen.add(value)
        candidates.append(value)

    if p12_password is not None:
        stripped = p12_password.strip()
        _add(stripped.encode("utf-8"))
        if stripped != p12_password:
            _add(p12_password.encode("utf-8"))
        try:
            _add(stripped.encode("latin-1"))
        except UnicodeEncodeError:
            pass
    _add(None)
    _add(b"")

    last_error: Exception | None = None
    for password in candidates:
        try:
            key, cert, _additional = pkcs12.load_key_and_certificates(
                p12_bytes,
                password,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
        if key is not None and cert is not None:
            return key, cert
        last_error = ValueError(
            "PKCS#12 did not contain a private key and certificate"
        )

    detail = str(last_error)[:200] if last_error else "unknown"
    raise ValueError(f"Invalid password or PKCS12 data ({detail})") from last_error


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
        from signxml.util import ds_tag
        from signxml.xades import XAdESDataObjectFormat, XAdESSignaturePolicy, XAdESSigner
    except ImportError as exc:
        raise RuntimeError("signxml is required for live XAdES signing") from exc

    class HaciendaXAdESSigner(XAdESSigner):
        """XAdES-EPES signer that emits C14N Transforms on policy/cert references.

        Hacienda verifiers expect explicit exclusive-C14N transforms on the
        SignedProperties and KeyInfo references (Chilkat/CRLibre style). Stock
        signxml digests those nodes but omits the Transform elements, which MH
        often reports as \"XML was modified after signing\".
        """

        def _add_reference_to_signed_info(self, sig_root, node_to_reference, **attrs):
            signed_info = self._find(sig_root, "SignedInfo")
            reference = SubElement(signed_info, ds_tag("Reference"), nsmap=self.namespaces)
            reference.set("URI", f"#{node_to_reference.get('Id')}")
            for attr_name, attr_value in attrs.items():
                reference.set(attr_name, attr_value)
            transforms = SubElement(reference, ds_tag("Transforms"), nsmap=self.namespaces)
            SubElement(
                transforms,
                ds_tag("Transform"),
                Algorithm=self.c14n_alg.value,
                nsmap=self.namespaces,
            )
            SubElement(
                reference,
                ds_tag("DigestMethod"),
                nsmap=self.namespaces,
                Algorithm=self.digest_alg.value,
            )
            digest_value_node = SubElement(
                reference, ds_tag("DigestValue"), nsmap=self.namespaces
            )
            node_c14n = self._c14n(node_to_reference, algorithm=self.c14n_alg)
            digest = self._get_digest(node_c14n, algorithm=self.digest_alg)
            digest_value_node.text = b64encode(digest).decode()

    key, cert = load_pkcs12_key_and_cert(p12_bytes, p12_password)

    root = etree.fromstring(xml_unsigned.encode("utf-8"))
    policy = XAdESSignaturePolicy(
        Identifier=settings.HACIENDA_XADES_POLICY_ID,
        Description=settings.HACIENDA_XADES_POLICY_DESCRIPTION,
        DigestMethod=DigestAlgorithm.SHA256,
        DigestValue=settings.HACIENDA_XADES_POLICY_DIGEST,
    )
    signer = HaciendaXAdESSigner(
        method=methods.enveloped,
        signature_policy=policy,
        data_object_format=XAdESDataObjectFormat(
            Description="FacturaElectronica",
            MimeType="text/xml",
        ),
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    signed_root = signer.sign(
        root,
        key=key,
        cert=cert.public_bytes(Encoding.PEM).decode("ascii"),
    )
    signed_xml = etree.tostring(
        signed_root,
        encoding="UTF-8",
        xml_declaration=True,
    ).decode("utf-8")
    return SignResult(xml_signed=signed_xml, mock=False)


def _mock_sign(xml_unsigned: str) -> SignResult:
    marker = "<!-- nidus-mock-xades-epes -->"
    if marker in xml_unsigned:
        return SignResult(xml_signed=xml_unsigned, mock=True)
    for close_tag in ("</FacturaElectronica>", "</MensajeReceptor>"):
        if close_tag in xml_unsigned:
            signed = xml_unsigned.replace(close_tag, f"{marker}{close_tag}", 1)
            return SignResult(xml_signed=signed, mock=True)
    raise ValueError("Unsigned XML is missing a supported root close tag")
