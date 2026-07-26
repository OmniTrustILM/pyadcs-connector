class DiscoveryHistoryRequestDto:
    def __init__(self, name: str = None, kind: str = None, page_number: int = 0, items_per_page: int = 100):
        self.name = name
        self.kind = kind
        self.page_number = page_number
        self.items_per_page = items_per_page

    def to_json(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "pageNumber": self.page_number,
            "itemsPerPage": self.items_per_page
        }

    @staticmethod
    def from_json(request_json: dict) -> "DiscoveryHistoryRequestDto":
        return DiscoveryHistoryRequestDto(
            request_json["name"],
            request_json["kind"],
            request_json["pageNumber"],
            request_json["itemsPerPage"]
        )
