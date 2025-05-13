from typing import Dict, Union
from pydantic import BaseModel
from common.crack_objects.PhoneNumber import PhoneNumberValidator

class CrackResult(BaseModel):
    range_start: PhoneNumberValidator
    range_end: PhoneNumberValidator
    results: Dict[str, Union[str, bool]]