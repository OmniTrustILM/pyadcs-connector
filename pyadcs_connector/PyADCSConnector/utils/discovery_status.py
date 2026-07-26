from enum import Enum


class DiscoveryStatus(Enum):
    IN_PROGRESS = "inProgress"
    FAILED = "failed"
    COMPLETED = "completed"
    WARNING = "warning"
