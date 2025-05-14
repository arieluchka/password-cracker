from common.models.Minion import Minion
from master.master_cracker_db.MasterCrackerDb import MasterCrackerDbInterface
from common.api_endpoints.MinionEndpoints import MinionEndpoints
import requests

# benefits?
#   organized
#   centalized logging?

class MinionCommunicator:
    def __init__(self, minion: Minion):
        self.minion = minion

        self.base_url = f"http://{minion.Ip}:{minion.Port}"

        self.__db = MasterCrackerDbInterface()

    def __get(self, path, foo):
        requests.get(
            url=self.base_url + path
        )

    # @property
    def get_minion_job_report(self, minion: Minion, job_assignment: JobAssignment) -> Job:
        """
        will send a GET for status of specific hash
        will return the Job
        """
        requests.get(
            MinionEndpoints
        )

        pass