import hashlib


def certificate_fingerprint(base64content: str) -> str:
    """SHA-256 hex of the exact base64 certificate string (UTF-8), matching the SQL
    encode(sha256(convert_to(base64content,'UTF8')),'hex') used by migration 0002.

    Accepted limitation: the exact string is hashed, with no decoding or
    normalization, so two byte-different base64 encodings of the same certificate
    (different line wrapping, trailing whitespace) yield different fingerprints and
    are stored as separate rows. This is deliberate -- it keeps Python and the
    migration's SQL byte-identical and cannot fail on malformed base64 -- and costs
    nothing in practice because ADCS returns each certificate in a stable encoding.
    """
    return hashlib.sha256(base64content.encode("utf-8")).hexdigest()
