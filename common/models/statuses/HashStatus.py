from enum import Enum


class HashStatus(Enum):
    UNCRACKED = "UnCracked"
    CRACKED = "Cracked"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "InProgress"