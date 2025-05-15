from common.models.statuses.MinionStatus import MinionStatus
from common.models.JobAssignment import JobAssignment
from common.crack_objects.Job import Job
from common.models.Minion import Minion
from typing import List
from master.master_cracker_db.MasterCrackerDb import MasterCrackerDbInterface
from master.MinionCommunicator import MinionCommunicator

class NewMasterCracker:
    def __init__(self):
        self.db = MasterCrackerDbInterface()

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

    def send_job_assignment_to_minion(self, minion: Minion):
        """will pick next scheduled job assignment from db, and send to minion ip and port"""
        job_assignment = self.db.get_scheduled_job_assignments(limit=1)[0]
        job_success = MinionCommunicator(minion).send_job_assignment(
            job_assignment
        )
        assert job_success # should always return true (if job was successful)



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


    def _check_and_update_job_assignment(self, minion: Minion, job_assignment: JobAssignment):
        """
        WONT REQUEST JOBASSIGNMENT ITSELF FROM DB, AS IT CAN BE CALLED FOR ONE MINION CHECK OR FOR MULTIPLE
        will _get_minion_job_report for every job assignment
        (?) if Job is done, update the jobass table (should also change minion status?).
        (?) trigger another call to g
        """
        minion_communicator = MinionCommunicator(minion=minion)
        minion_job = minion_communicator.get_job_report(job_assignment)
        ...
        pass

    def _get_minion_job_report(self, minion: Minion, job_assignment: JobAssignment) -> Job:
        """
        will send a GET for status of specific hash
        will return the Job
        """
        pass

# todo: create seperate class of MinionCommunicator?
# yes, so there will also be centrelized place for Raising Exceptions and handling them?
# if adding MinionCommunicator, make it update db every time it had successful interaction (then health-check job will skip checking recently communicated minions)