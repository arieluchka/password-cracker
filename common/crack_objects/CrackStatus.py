from typing import Dict, Union, Any
from pydantic import BaseModel


class CrackStatus(BaseModel):
    status: str = "IDLE"  # IDLE, IN_PROGRESS, COMPLETED, ERROR
    hashes: Dict[str, Union[str, bool]] = {}
