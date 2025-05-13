from common.models.statuses.MinionStatus import MinionStatus

class Minion:
    def __init__(self, Id, Ip, Port, Status=MinionStatus.AVAILABLE, LastSeen=None, FailedHealthChecks=0):
        self.Id = Id
        self.Ip = Ip
        self.Port = Port

        # Accept both Enum and string for Status
        if isinstance(Status, str):
            try:
                self.Status = MinionStatus(Status)
            except ValueError:
                self.Status = MinionStatus.AVAILABLE
        else:
            self.Status = Status
        self.LastSeen = LastSeen
        self.FailedHealthChecks = FailedHealthChecks

    def __repr__(self):
        return (f"Minion(Id={self.Id}, Ip='{self.Ip}', Port={self.Port}, Status='{self.Status.name}', "
                f"LastSeen={self.LastSeen}, FailedHealthChecks={self.FailedHealthChecks})")
