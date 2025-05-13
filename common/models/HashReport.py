from typing import Optional, List, Dict, Any

class HashReport:
    def __init__(
        self,
        hash_id: int,
        hash_value: str,
        password: Optional[str] = None,
        status: str = "Unknown",
        total_jobs: Optional[int] = None,
        completed_jobs: Optional[int] = None,
        creation_time: Optional[str] = None,
        crack_time: Optional[str] = None
    ):
        self.hash_id = hash_id
        self.hash_value = hash_value
        self.password = password
        self.status = status
        self.total_jobs = total_jobs
        self.completed_jobs = completed_jobs
        self.creation_time = creation_time
        self.crack_time = crack_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash_id": self.hash_id,
            "hash_value": self.hash_value,
            "password": self.password,
            "status": self.status,
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "creation_time": self.creation_time,
            "crack_time": self.crack_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HashReport':
        return cls(
            hash_id=data.get("hash_id"),
            hash_value=data.get("hash_value"),
            password=data.get("password"),
            status=data.get("status"),
            total_jobs=data.get("total_jobs"),
            completed_jobs=data.get("completed_jobs"),
            creation_time=data.get("creation_time"),
            crack_time=data.get("crack_time")
        )