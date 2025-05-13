from dataclasses import dataclass
from typing import Optional
from .statuses.JobAssignmentStatus import JobAssignmentStatus

@dataclass
class JobAssignment:
    Id: int
    HashId: int
    StartRange: str
    EndRange: str
    Status: JobAssignmentStatus = JobAssignmentStatus.SCHEDULED
    MinionId: Optional[int] = None
    AssignmentTime: Optional[str] = None
    CompletionTime: Optional[str] = None
