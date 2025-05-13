from dataclasses import dataclass
from typing import Optional

@dataclass
class HashEntry:
    hash: str
    password: Optional[str] = False
    
    def is_cracked(self) -> bool:
        return self.password is not None
    
    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "password": self.password
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HashEntry':
        return cls(
            hash=data["hash"],
            password=data.get("password")
        )