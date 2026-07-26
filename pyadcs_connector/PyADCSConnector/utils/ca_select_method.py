from enum import Enum


class CaSelectMethod(Enum):
    def __init__(self, method: str, description: str):
        self.method = method
        self.description = description

    SEARCH = "search", "Search for all available CAs"
    CONFIGSTRING = "configstring", "Use the ConfigString to select existing CA"

    @staticmethod
    def from_string(method: str) -> 'CaSelectMethod':
        return {
            "search": CaSelectMethod.SEARCH,
            "configstring": CaSelectMethod.CONFIGSTRING
        }.get(method, CaSelectMethod.SEARCH)
