from pydantic import BaseModel, validator
import ipaddress


class NewMinion(BaseModel):
    Ip: str
    Port: int

    @validator('Port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    @validator('Ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')