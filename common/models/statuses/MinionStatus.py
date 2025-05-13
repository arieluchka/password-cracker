from enum import Enum


class MinionStatus(Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "UnAvailable"
    BUSY = "Busy"