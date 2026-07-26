class DiscoveryCertificateDto:
    def __init__(self, uuid: str, base64_content: str, meta: list[dict]):
        self.uuid = uuid
        self.base64_content = base64_content
        self.meta = meta

    def to_json(self):
        return {
            "uuid": self.uuid,
            "base64Content": self.base64_content,
            "meta": self.meta
        }
