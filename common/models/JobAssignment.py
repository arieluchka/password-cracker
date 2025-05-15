from dataclasses import dataclass
from typing import Optional
from .statuses.JobStatus import JobStatus

@dataclass
class JobAssignment:
    Id: int
    HashId: int
    StartRange: str
    EndRange: str
    Status: JobStatus = JobStatus.SCHEDULED
    MinionId: Optional[int] = None
    AssignmentTime: Optional[str] = None
    CompletionTime: Optional[str] = None
