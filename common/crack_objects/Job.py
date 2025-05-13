from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    Id: int
    StartRange: str
    EndRange: str
    Status: str
    HashId: Optional[int] = None
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