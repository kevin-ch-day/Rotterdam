"""Utilities to extract and validate APK signing certificates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from cryptography import x509
from cryptography.hazmat.primitives import hashes

try:  # pragma: no cover - optional dependency
    from apksigtool import (
        APKSignatureSchemeBlock,
        extract_v2_sig,
        parse_apk_signing_block,
    )
except Exception as e:  # pragma: no cover
    raise ImportError("apksigtool is required for certificate analysis") from e


def _extract_certificates(apk_path: str | Path) -> List[x509.Certificate]:
    """Return a list of signing certificates found in ``apk_path``.

    The function attempts to parse APK Signature Scheme v2/v3 blocks using
    ``apksigtool``. If the tool is unavailable or parsing fails an empty list is
    returned.
    """

    if not extract_v2_sig or not parse_apk_signing_block or not APKSignatureSchemeBlock:
        return []

    certs: List[x509.Certificate] = []
    try:
        _, sig_block = extract_v2_sig(str(apk_path))
        for pair in parse_apk_signing_block(sig_block).pairs:
            block = pair.value
            if not isinstance(block, APKSignatureSchemeBlock):
                continue
            for signer in block.signers:
                for cert in signer.signed_data.certificates:
                    try:
                        certs.append(x509.load_der_x509_certificate(cert.data))
                    except Exception:
                        continue
    except Exception:
        return []
    return certs


def analyze_certificates(apk_path: str | Path) -> Dict[str, object]:
    """Extract signing certificates and derive basic trust metrics.

    Parameters
    ----------
    apk_path:
        Path to the APK file whose certificates should be inspected.

    Returns
    -------
    dict
        ``{"certificates": list[dict], "expired": bool, "self_signed": bool}``

    Each certificate entry includes subject, issuer, validity window,
    SHA-256 fingerprint and flags for whether it is expired or self-signed.
    Aggregated ``expired`` and ``self_signed`` fields are ``True`` when any
    certificate exhibits the respective property.
    """

    certs = _extract_certificates(apk_path)
    info: List[Dict[str, object]] = []
    any_expired = False
    any_self_signed = False
    now = datetime.now(timezone.utc)

    for cert in certs:
        subject = cert.subject.rfc4514_string()
        issuer = cert.issuer.rfc4514_string()
        expired = cert.not_valid_after < now
        self_signed = subject == issuer
        any_expired |= expired
        any_self_signed |= self_signed
        info.append(
            {
                "subject": subject,
                "issuer": issuer,
                "not_before": cert.not_valid_before.isoformat(),
                "not_after": cert.not_valid_after.isoformat(),
                "expired": expired,
                "self_signed": self_signed,
                "sha256_fingerprint": cert.fingerprint(hashes.SHA256()).hex().upper(),
            }
        )

    return {"certificates": info, "expired": any_expired, "self_signed": any_self_signed}


__all__ = ["analyze_certificates"]
