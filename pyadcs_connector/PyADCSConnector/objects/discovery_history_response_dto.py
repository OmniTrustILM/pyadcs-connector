from PyADCSConnector.objects.discovery_certificate_dto import DiscoveryCertificateDto
from PyADCSConnector.utils.discovery_status import DiscoveryStatus


class DiscoveryHistoryResponseDto:
    def __init__(self, name: str = None, uuid: str = None, status: DiscoveryStatus = DiscoveryStatus.IN_PROGRESS,
                 certificate_data: list[DiscoveryCertificateDto] = None, meta: list[dict] = None,
                 total_certificates_discovered: int = 0):
        self.name = name
        self.uuid = uuid
        self.status = status
        self.certificate_data = certificate_data
        self.meta = meta
        self.total_certificates_discovered = total_certificates_discovered

    def to_json(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "status": self.status,
            "certificateData": [certificate for certificate in self.certificate_data],
            "meta": self.meta,
            "totalCertificatesDiscovered": self.total_certificates_discovered
        }
