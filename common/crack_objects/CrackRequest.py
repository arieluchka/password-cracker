from typing import List
from pydantic import BaseModel
from .PhoneNumber import PhoneNumberValidator
from common.config.HashesTypes import HashTypes


class CrackRequest(BaseModel):
    hashes: List[str]
    start_range: PhoneNumberValidator
    end_range: PhoneNumberValidator
    hash_type: HashTypes=HashTypes.MD5.value

