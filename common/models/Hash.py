from common.models.statuses.HashStatus import HashStatus

class Hash:
    def __init__(self, HashId, HashValue, Password, Status, CreationTime=None, CrackTime=None):
        self.HashId = HashId
        self.HashValue = HashValue
        self.Password = Password
        self.Status = HashStatus(Status) if Status else None
        self.CreationTime = CreationTime
        self.CrackTime = CrackTime

    def __repr__(self):
        return f"<Hash(HashId={self.HashId}, HashValue='{self.HashValue}', Password='{self.Password}', Status='{self.Status}', CreationTime='{self.CreationTime}', CrackTime='{self.CrackTime}')>"
