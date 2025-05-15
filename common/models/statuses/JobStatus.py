from enum import Enum

# todo: add reschedule status?
# todo: decide on final statuses and remove extras
class JobStatus(Enum):
    SCHEDULED = "Scheduled"
    UNSCHEDULED = "UnScheduled"
    ASSIGNED = "Assigned"
    INPROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"
