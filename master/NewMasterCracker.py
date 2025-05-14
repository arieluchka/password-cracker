from common.models.statuses.MinionStatus import MinionStatus
from common.models.JobAssignment import JobAssignment
from common.crack_objects.Job import Job
from common.models.Minion import Minion
from typing import List


class NewMasterCracker:
    def __init__(self):
        pass


    def send_job_assignment_to_minion(self, minion_ip, minion_port):
        """will pick next scheduled job assignment from db, and send to minion ip and port"""
        pass

    def send_job_assignments_to_all_free_minions(self, minions_list = List[Minion]):
        """
        1) get all free
        """
        pass

    def get_all_free_minions(self):
        """
        get minion list from db.
        check status of every minion.

        """

    def _check_minion_status(self, minion: Minion) -> MinionStatus:
        """
        send GET status to minion and return its status
        """

    def check_and_update_status_of_all_minions(self) -> List[Minion]:
        """
        get all minions from db.
        _check_minion_status for each.
        if status in db busy but real status is available,
        """



    def check_minion_job_assignments(self, minion_id):
        pass

    def _get_minion_job_report(self, minion: Minion, job_assignment: JobAssignment) -> Job:
        """
        will send a GET for status of specific hash
        will return the Job
        """
        pass

# todo: create seperate class of MinionCommunicator?