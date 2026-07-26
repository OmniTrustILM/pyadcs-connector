from enum import Enum


class CertificateRevocationReason(Enum):
    UNSPECIFIED = "unspecified"
    KEY_COMPROMISE = "keyCompromise"
    CA_COMPROMISE = "cACompromise"
    AFFILIATION_CHANGED = "affiliationChanged"
    SUPERSEDED = "superseded"
    CESSATION_OF_OPERATION = "cessationOfOperation"
    CERTIFICATE_HOLD = "certificateHold"
    PRIVILEGES_WITHDRAWN = "privilegeWithdrawn"
    AA_COMPROMISE = "aACompromise"

    @staticmethod
    def from_string(reason: str) -> 'CertificateRevocationReason':
        return {
            "unspecified": CertificateRevocationReason.UNSPECIFIED,
            "keyCompromise": CertificateRevocationReason.KEY_COMPROMISE,
            "cACompromise": CertificateRevocationReason.CA_COMPROMISE,
            "affiliationChanged": CertificateRevocationReason.AFFILIATION_CHANGED,
            "superseded": CertificateRevocationReason.SUPERSEDED,
            "cessationOfOperation": CertificateRevocationReason.CESSATION_OF_OPERATION,
            "certificateHold": CertificateRevocationReason.CERTIFICATE_HOLD,
            "privilegeWithdrawn": CertificateRevocationReason.PRIVILEGES_WITHDRAWN,
            "aACompromise": CertificateRevocationReason.AA_COMPROMISE
        }.get(reason, CertificateRevocationReason.UNSPECIFIED)

    def to_string_ps_value(self) -> str:
        return {
            CertificateRevocationReason.UNSPECIFIED: "Unspecified",
            CertificateRevocationReason.KEY_COMPROMISE: "KeyCompromise",
            CertificateRevocationReason.CA_COMPROMISE: "CACompromise",
            CertificateRevocationReason.AFFILIATION_CHANGED: "AffiliationChanged",
            CertificateRevocationReason.SUPERSEDED: "Superseded",
            CertificateRevocationReason.CESSATION_OF_OPERATION: "CeaseOfOperation",
            CertificateRevocationReason.CERTIFICATE_HOLD: "Hold",
            CertificateRevocationReason.PRIVILEGES_WITHDRAWN: "Unspecified",
            CertificateRevocationReason.AA_COMPROMISE: "Unspecified"
        }.get(self, "Unspecified")
