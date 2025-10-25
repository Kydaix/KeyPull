"""Parsing and validation utilities for Android keybox XML files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET


@dataclass
class Certificate:
    format: str
    data: str


@dataclass
class CertificateChain:
    number_of_certificates: int
    certificates: List[Certificate] = field(default_factory=list)


@dataclass
class PrivateKey:
    format: str
    data: str


@dataclass
class Key:
    algorithm: str
    private_key: PrivateKey
    certificate_chain: CertificateChain


@dataclass
class Keybox:
    device_id: str
    keys: List[Key] = field(default_factory=list)


@dataclass
class Attestation:
    number_of_keyboxes: int
    keyboxes: List[Keybox] = field(default_factory=list)


class KeyboxValidationError(RuntimeError):
    """Raised when a keybox file cannot be parsed."""


def _parse_certificate(element: ET.Element) -> Certificate:
    return Certificate(
        format=element.get("format", ""),
        data=(element.text or "").strip(),
    )


def _parse_certificate_chain(element: ET.Element) -> CertificateChain:
    count_text = element.findtext("NumberOfCertificates", default="0")
    try:
        count = int(count_text)
    except ValueError:
        raise KeyboxValidationError(
            f"Invalid NumberOfCertificates value: {count_text!r}"
        ) from None
    certificates = [
        _parse_certificate(cert_el)
        for cert_el in element.findall("Certificate")
    ]
    return CertificateChain(number_of_certificates=count, certificates=certificates)


def _parse_private_key(element: ET.Element) -> PrivateKey:
    return PrivateKey(
        format=element.get("format", ""),
        data=(element.text or "").strip(),
    )


def _parse_key(element: ET.Element) -> Key:
    private_key_el = element.find("PrivateKey")
    certificate_chain_el = element.find("CertificateChain")
    if private_key_el is None or certificate_chain_el is None:
        raise KeyboxValidationError("Key entry is missing PrivateKey or CertificateChain element")
    return Key(
        algorithm=element.get("algorithm", ""),
        private_key=_parse_private_key(private_key_el),
        certificate_chain=_parse_certificate_chain(certificate_chain_el),
    )


def _parse_keybox(element: ET.Element) -> Keybox:
    return Keybox(
        device_id=element.get("DeviceID", ""),
        keys=[_parse_key(key_el) for key_el in element.findall("Key")],
    )


def _parse_attestation(root: ET.Element) -> Attestation:
    count_text = root.findtext("NumberOfKeyboxes", default="0")
    try:
        number_of_keyboxes = int(count_text)
    except ValueError:
        raise KeyboxValidationError(f"Invalid NumberOfKeyboxes value: {count_text!r}") from None
    keyboxes = [_parse_keybox(kb_el) for kb_el in root.findall("Keybox")]
    return Attestation(number_of_keyboxes=number_of_keyboxes, keyboxes=keyboxes)


def validate(path: Path) -> Attestation:
    """Validate a keybox XML file and return its parsed contents.

    The function mirrors the Go implementation by printing a concise summary
    of the extracted metadata. The parsed :class:`Attestation` object is
    returned for further processing.
    """

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise KeyboxValidationError(f"Failed to read keybox file: {exc}") from exc

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise KeyboxValidationError(f"XML is invalid: {exc}") from exc

    attestation = _parse_attestation(root)

    print(f"Keyboxes found: {attestation.number_of_keyboxes}")
    for index, keybox in enumerate(attestation.keyboxes, start=1):
        print(f"Keybox {index} - Device ID: {keybox.device_id}")
        for key_index, key in enumerate(keybox.keys, start=1):
            print(
                "  Key {idx}: Algorithm={alg}, Certificates={count}".format(
                    idx=key_index,
                    alg=key.algorithm or "unknown",
                    count=key.certificate_chain.number_of_certificates,
                )
            )

    return attestation
