from common.models.Minion import Minion
from master.master_cracker_db.MasterCrackerDb import MasterCrackerDbInterface
from common.api_endpoints.MinionEndpoints import MinionEndpoints
from common.models.MinionHealth import MinionHealth
from common.models.JobAssignment import JobAssignment
from common.crack_objects.Job import Job
import requests

# benefits
#   organized
#   centalized logging?

class MinionCommunicator:
    def __init__(self, minion: Minion):
        self.minion = minion

        self.base_url = f"http://{minion.Ip}:{minion.Port}"

        self.__db = MasterCrackerDbInterface()

    def get_job_report(self, job_assignment: JobAssignment) -> Job:
        """
        will send a GET for status of specific hash
        will return the Job
        """
        requests.get(
            url=MinionEndpoints.GET.STATUS.format(
                status="",
                start_range="",
                end_range="",
            )
        )

    def send_job_assignment(self, job_assignment: JobAssignment) -> bool:
        # MinionEndpoints.POST.CRACK
        # HAVE ERROR RAISES?
        ...



    def get_health(self) -> MinionHealth:
        # MinionEndpoints.GET.HEALTH
        res = MinionHealth()
        return res