from dataclasses import dataclass
from typing import Optional
from common.models.statuses.JobStatus import JobStatus

@dataclass
class Job:
    Id: int
    StartRange: str
    EndRange: str
    Status: JobStatus | str # todo: change all occourances to use JobAssignmentStatus
    HashId: Optional[int] = None # remove hash id?
    HashValue: Optional[str] = None
    
    def is_finished(self) -> bool:
        return self.Status == "Completed"
    
    def is_in_progress(self) -> bool:
        return self.Status == "InProgress"
    
    def to_dict(self) -> dict:
        return {
            "Id": self.Id,
            "StartRange": self.StartRange,
            "EndRange": self.EndRange,
            "Status": self.Status,
            "HashId": self.HashId,
            "HashValue": self.HashValue
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Job':
        return cls(
            Id=data["Id"],
            StartRange=data["StartRange"],
            EndRange=data["EndRange"],
            Status=data["Status"],
            HashId=data.get("HashId"),
            HashValue=data.get("HashValue")
        )