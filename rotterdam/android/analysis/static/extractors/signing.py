"""APK signature validation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from apksigtool import (
    APKSignatureSchemeBlock,
    VerificationError,
    extract_v2_sig,
    parse_apk_signing_block,
    verify_apk_signature_scheme_v2,
    verify_apk_signature_scheme_v3,
)

# Path to the default trust store containing trusted certificate fingerprints.
TRUST_STORE_PATH = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "trust_stores"
    / "android.json"
)


def _load_trusted_fingerprints(path: Path | None = None) -> List[str]:
    """Load trusted certificate fingerprints from ``path``.

    Parameters
    ----------
    path:
        Optional path to a JSON file containing a list under the key
        ``"trusted_fingerprints"``.  If the file is missing or malformed an
        empty list is returned.
    """

    path = path or TRUST_STORE_PATH
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return []
    fingerprints = data.get("trusted_fingerprints", [])
    # Normalise to uppercase hexadecimal strings for comparison.
    return [fp.upper() for fp in fingerprints if isinstance(fp, str)]


def verify_signature(
    apk_path: str | Path,
    *,
    trust_store: str | Path | None = None,
) -> Dict[str, object]:
    """Validate the APK's signature and compare against a trust store.

    Parameters
    ----------
    apk_path:
        Path to the APK file to inspect.
    trust_store:
        Optional path to an alternate trust store.  Defaults to
        ``analysis/trust_store.json``.

    Returns
    -------
    dict
        ``{"valid": bool, "trusted": bool, "fingerprints": list[str]}``

    The ``valid`` field indicates if the APK's v2/v3 signature verified
    successfully. ``trusted`` will be ``True`` when any certificate fingerprint
    matches an entry in the trust store.
    """

    apk_path = Path(apk_path)
    fingerprints: List[str] = []
    valid = False

    try:
        # ``extract_v2_sig`` returns the offset of the signing block and the raw
        # data for further parsing.  This covers both APK Signature Scheme v2 and
        # v3 as they share the same container format.
        _, sig_block = extract_v2_sig(str(apk_path))
        for pair in parse_apk_signing_block(sig_block).pairs:
            block = pair.value
            if not isinstance(block, APKSignatureSchemeBlock):
                continue
            try:
                if block.is_v2():
                    verify_apk_signature_scheme_v2(block.signers, str(apk_path))
                else:
                    verify_apk_signature_scheme_v3(block.signers, str(apk_path))
            except VerificationError:
                valid = False
                break
            else:
                valid = True
                for signer in block.signers:
                    for cert in signer.signed_data.certificates:
                        try:
                            cert_obj = x509.load_der_x509_certificate(cert.data)
                            fp = cert_obj.fingerprint(hashes.SHA256()).hex().upper()
                            fingerprints.append(fp)
                        except Exception:
                            continue
    except Exception:
        valid = False

    trusted_fps = _load_trusted_fingerprints(
        Path(trust_store) if trust_store else TRUST_STORE_PATH
    )
    trusted = any(fp in trusted_fps for fp in fingerprints)

    return {"valid": valid, "trusted": trusted, "fingerprints": fingerprints}


__all__ = ["verify_signature", "TRUST_STORE_PATH"]
