from PyADCSConnector.utils.certificate_type import CertificateType


class CertificateDto:
    def __init__(self, certificate_data: str, uuid: str or None, meta: list[dict] or None,
                 certificate_type: CertificateType = CertificateType.X509):
        self.certificate_data = certificate_data
        self.uuid = uuid
        self.meta = meta
        self.certificate_type = certificate_type

    def to_json(self):
        return {
            "certificateData": self.certificate_data,
            "uuid": self.uuid,
            "meta": self.meta,
            "certificateType": self.certificate_type
        }
