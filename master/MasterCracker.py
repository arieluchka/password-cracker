import hashlib
import os
import threading
import time
from typing import List

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks

from common.crack_objects.CrackRequest import CrackRequest
from common.crack_objects.CrackResult import CrackResult
from common.crack_objects.PhoneNumber import PhoneNumberValidator
from common.models.JobAssignment import JobAssignment
from common.models.Minion import Minion
from common.models.NewMinion import NewMinion
from common.models.statuses.HashStatus import HashStatus
from common.models.statuses.JobAssignmentStatus import JobAssignmentStatus
from common.models.statuses.MinionStatus import MinionStatus
from common.phone_ranges import _ranges_for_jobs_generator, efficient_phone_num_range, phone_num_range
from master.master_cracker_db.MasterCrackerDb import MasterCrackerDbInterface

# change this if you want to hash by num order (and not by efficient order)
PHONE_NUM_RANGES = efficient_phone_num_range

app = FastAPI()
DEFAULT_IP = os.environ.get("DEFAULT_IP", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", 5000))

HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", 10))
SET_MINION_TO_UNAVAILABLE_AFTER_HEALTH_CHECK = int(os.environ.get("SET_MINION_TO_UNAVAILABLE_AFTER_HEALTH_CHECK", 5))
MAX_FAILED_HEALTH_CHECKS = int(os.environ.get("MAX_FAILED_HEALTH_CHECKS", 0))

PASSWORDS_PER_JOB = int(os.environ.get("PASSWORDS_PER_JOB", 100000))

master_cracker = None


def get_master_cracker():
    global master_cracker
    if master_cracker is None:
        master_cracker = MasterCracker()
    return master_cracker


class MasterCracker:
    def __init__(self):
        self.db = MasterCrackerDbInterface()
        self.__create_master_cracker_db()

        self.health_check_thread = None
        self.job_scan_thread = None
        self.job_assignment_thread = None

        self.health_check_running = False
        self.job_scan_running = False
        self.job_assignment_running = False

        self.start_scheduled_tasks()

    def __create_master_cracker_db(self):
        if not os.path.exists(self.db.db_path) or not self.db.check_tables_exist():
            self.db.create_tables()

    def start_scheduled_tasks(self):
        if not self.health_check_thread or not self.health_check_thread.is_alive():
            self.health_check_thread = threading.Thread(target=self.periodic_health_check, daemon=True)
            self.health_check_thread.start()

        if not self.job_assignment_running or not self.job_assignment_thread.is_alive():
            self.job_assignment_thread = threading.Thread(target=self.periodic_job_assignments, daemon=True)
            self.job_assignment_thread.start()

        if not self.job_scan_thread or not self.job_scan_thread.is_alive():
            self.job_scan_thread = threading.Thread(target=self.periodic_in_progress_jobs_scan, daemon=True)
            self.job_scan_thread.start()

    # region Scheduled Tasks

    def periodic_health_check(self):
        self.health_check_running = True
        while self.health_check_running:
            minions = self.db.get_all_minions()
            for minion in minions:
                minion_id = minion.Id
                ip = minion.Ip
                port = minion.Port
                reported_status = self.check_minion_health(ip, port)
                if reported_status:
                    if reported_status == MinionStatus.AVAILABLE.value and minion.Status == MinionStatus.BUSY:
                        self.db.update_minion_status(minion_id=minion.Id, status=MinionStatus.AVAILABLE.value)
                    elif minion.Status == MinionStatus.UNAVAILABLE:
                        self.db.update_minion_status_and_failed_checks(
                            minion_id,
                            MinionStatus.AVAILABLE.value,
                            0
                        )
                    else:
                        self.db.update_failed_checks_to_zero(minion_id,)

                else:
                    self.__update_minion_as_not_seen(minion_id)

            time.sleep(HEALTH_CHECK_INTERVAL)

    def __in_progress_jobs_scan(self):
        in_progress_jobs = self.db.get_all_in_progress_jobs()
        if not in_progress_jobs:
            return 0

        jobs_completed = 0
        jobs_rescheduled = 0

        for job in in_progress_jobs:
            job_id = job[0]
            hash_id = job[1]
            minion_id = job[2]
            start_range = job[3]
            end_range = job[4]
            hash_value = job[5]

            minion = self.db.get_minion_by_id(minion_id)
            if not minion:
                continue

            try:
                status_url = f"http://{minion.Ip}:{minion.Port}/status/{hash_value}/{start_range}/{end_range}"
                response = requests.get(status_url, timeout=3)

                if response.status_code == 200:
                    status_data = response.json()

                    if status_data.get("status") == "Completed":
                        results = {}
                        hashes_data = status_data.get("hashes", {})

                        for hash_val, result in hashes_data.items():
                            results[hash_val] = result

                        crack_result = CrackResult(
                            range_start=PhoneNumberValidator(phone_number=start_range),
                            range_end=PhoneNumberValidator(phone_number=end_range),
                            results=results
                        )

                        self.complete_job_assignment(crack_result)
                        jobs_completed += 1
                elif response.status_code == 404:
                    # Job not found on minion - reschedule it
                    print(f"Job {job_id} not found on minion {minion.Ip}:{minion.Port}. Rescheduling...")
                    self.db.update_job_assignment(job_id, None, JobAssignmentStatus.SCHEDULED.value)
                    self.db.update_minion_status(minion_id, MinionStatus.AVAILABLE.value)
                    jobs_rescheduled += 1

            except requests.RequestException as e:
                print(f"Error checking job status for job {job_id} with minion {minion.Ip}:{minion.Port}: {e}")
                
                if isinstance(e, (requests.ConnectionError, requests.Timeout)):
                    print(f"Minion {minion.Ip}:{minion.Port} is unreachable. Rescheduling job {job_id}...")
                    self.db.update_job_assignment(job_id, None, JobAssignmentStatus.SCHEDULED.value)
                    
                    self.__update_minion_as_not_seen(minion_id)
                    jobs_rescheduled += 1
            except ValueError as e:
                print(f"Error checking job status for job {job_id} with minion {minion.Ip}:{minion.Port}: {e}")

        # If any jobs were rescheduled, trigger job assignment
        if jobs_rescheduled > 0:
            print(f"Rescheduled {jobs_rescheduled} jobs. Triggering job assignment...")
            self.send_jobs_to_available_minions()

        return jobs_completed

    def periodic_in_progress_jobs_scan(self):
        self.job_scan_running = True
        job_scan_interval = int(os.environ.get("JOB_SCAN_INTERVAL", 30))

        while self.job_scan_running:
            try:
                jobs_completed = self.__in_progress_jobs_scan()
                if jobs_completed > 0:
                    print(f"Job scan completed: {jobs_completed} jobs finished")
            except Exception as e:
                print(f"Error in job scan: {e}")

            time.sleep(job_scan_interval)

    def periodic_job_assignments(self):
        self.job_assignment_running = True
        job_assignment_interval = int(os.environ.get("JOB_ASSIGNMENT_INTERVAL", 30))

        while self.job_assignment_running:
            try:
                sent_jobs = self.send_jobs_to_available_minions()
                if sent_jobs > 0:
                    print(f"Periodic Job Assignment completed: {sent_jobs} sent to minions")
            except Exception as e:
                print(f"Error in job scan: {e}")

            time.sleep(job_assignment_interval)

    # endregion

    def __update_minion_as_not_seen(self, minion_id):
        minion = self.db.get_minion_by_id(minion_id)
        minion_health_check = minion.FailedHealthChecks + 1
        if minion_health_check >= SET_MINION_TO_UNAVAILABLE_AFTER_HEALTH_CHECK and minion.Status != MinionStatus.UNAVAILABLE:
            self.db.update_minion_status_and_failed_checks_no_lastseen(
                minion_id,
                MinionStatus.UNAVAILABLE.value,
                minion_health_check
            )
            self.db.reschedule_inprogress_jobs_for_minion(minion_id)
        else:
            self.db.update_minion_failed_checks(
                minion_id,
                minion_health_check
            )

    def check_minion_health(self, ip, port):
        health_url = f"http://{ip}:{port}/health"
        try:
            resp = requests.get(health_url, timeout=3)
            if resp.status_code == 200:
                return resp.json().get("status")
        except Exception:  # todo: change to timeout exception
            pass
        return False

    def add_new_hashes(self, hash_list):
        count = 0
        for hash_value in hash_list:
            if not self.db.check_hash_exists(hash_value):
                self.db.add_new_hash(hash_value)
                count += 1

        return count

    # Todo: dont create all at once. track last generated range, and create a function to get the next range.
    def create_new_job_assignments(self):
        scheduled_hashes = self.db.get_scheduled_hashes()
        if not scheduled_hashes:
            return 0

        job_assignments_created = 0

        for hash_entry in scheduled_hashes:
            hash_id = hash_entry["HashId"]

            try:
                batch_values = []
                for start_range, end_range in _ranges_for_jobs_generator(password_ranges=PHONE_NUM_RANGES,
                                                                         passwords_per_job=PASSWORDS_PER_JOB):
                    batch_values.append((int(hash_id), str(start_range), str(end_range)))

                if batch_values:
                    inserted = self.db.batch_create_job_assignments(batch_values)
                    if inserted:
                        job_assignments_created += inserted

                self.db.update_hash_status(hash_id, HashStatus.IN_PROGRESS.value)

            except (ValueError, TypeError) as e:
                print(f"Error in batch job creation for hash ID {hash_id}: {e}")

        return job_assignments_created

    def send_job_to_minion(self, minion: Minion, job: JobAssignment) -> bool:
        """
        returns true if successfully sent to minion, false if minion unavailable
        """
        minion_health = self.check_minion_health(minion.Ip, minion.Port)

        if minion_health:
            hash_value = self.db.get_hash_by_id(job.HashId)
            if not hash_value:
                return False

            crack_request_obj = CrackRequest(
                hashes=[hash_value.HashValue],
                start_range=PhoneNumberValidator(phone_number=job.StartRange),
                end_range=PhoneNumberValidator(phone_number=job.EndRange)
            )

            try:
                response = requests.post(
                    f"http://{minion.Ip}:{minion.Port}/crack",
                    json=crack_request_obj.model_dump(),
                    timeout=5
                )
                if response.status_code == 200:
                    self.db.update_job_assignment(job.Id, minion.Id, JobAssignmentStatus.INPROGRESS.value)
                    self.db.update_minion_status(minion.Id, MinionStatus.BUSY.value)
                    return True
            except requests.exceptions.RequestException:
                pass
        return False

    def send_jobs_to_available_minions(self):
        available_minions = self.db.get_all_available_minions()
        if not available_minions:
            return 0

        scheduled_jobs = self.db.get_scheduled_job_assignments(limit=len(available_minions))
        if not scheduled_jobs:
            return 0

        jobs_assigned = 0

        for job in scheduled_jobs:
            job_assigned = False
            for minion in available_minions:
                if minion.Status != MinionStatus.AVAILABLE:  # Skip minions that became unavailable
                    continue

                if self.send_job_to_minion(minion, job):
                    jobs_assigned += 1
                    job_assigned = True
                    available_minions.remove(
                        minion)  # Remove minion from available pool #todo: verify if its the correct thing (index shift)
                    break

            if not job_assigned:
                # If no minion could take this job, stop trying further jobs
                break

            if not available_minions:
                # If no more available minions, stop processing jobs
                break

        return jobs_assigned

    def calculate_hash(self, password: str) -> str:  # todo: move to common area
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    def __verify_password_of_hash(self, needed_hash: str, found_password: str) -> bool:
        password_hash = self.calculate_hash(password=found_password)
        return password_hash == needed_hash

    def add_found_password_to_hash(self, hash_id: int, password: str) -> bool:
        hash_entry = self.db.get_hash_by_id(hash_id)
        if not hash_entry:
            return False

        if not self.__verify_password_of_hash(hash_entry.HashValue, password):
            return False

        self.db.update_hash_with_password(hash_id, password)
        self.db.delete_jobs_by_hash_id(hash_id)
        return True

    def complete_job_assignment(self, crack_result: CrackResult):
        for hash_value, result in crack_result.results.items():
            hash_entry = self.db.get_hash_by_value(hash_value)
            if not hash_entry:
                continue

            job = self.db.get_job_assignment(
                hash_id=hash_entry.HashId,
                start_range=str(crack_result.range_start),
                end_range=str(crack_result.range_end)
            )
            if not job:
                continue

            if isinstance(result, bool):
                self.db.update_minion_status(job.MinionId, MinionStatus.AVAILABLE.value)
                self.db.mark_job_assignment_completed(job.Id)
                self.send_jobs_to_available_minions()
            elif isinstance(result, str):  # Password was found
                self.add_found_password_to_hash(hash_entry.HashId, result)
                self.db.update_minion_status(job.MinionId, MinionStatus.AVAILABLE.value)
                self.db.mark_job_assignment_completed(job.Id)

    def add_new_minion(self, new_minion: NewMinion):
        if self.db.minion_exists(new_minion.Ip, new_minion.Port):
            raise HTTPException(status_code=409, detail="Minion with this IP and port already exists")
        if not self.check_minion_health(new_minion.Ip, new_minion.Port):
            raise HTTPException(status_code=400,
                                detail="Minion health check failed or could not reach minion at provided IP/port")
        minion_id = self.db.register_new_minion(new_minion.Ip, new_minion.Port)
        if not minion_id:
            raise HTTPException(status_code=500, detail="Failed to register minion")
        return minion_id

    def get_hash_reports(self):
        hash_reports = self.db.get_hash_reports()
        return hash_reports


# todo: validate input for every endpoint
@app.post("/add-minion")  # todo: also accept local host
def add_minion(new_minion: NewMinion):
    master = get_master_cracker()
    minion_id = master.add_new_minion(new_minion)
    return {"status": "success", "minion_id": minion_id}


@app.get("/get-minions-status")
def get_minions_status():
    master = get_master_cracker()
    minions = master.db.get_all_minions()
    return [
        {
            "Id": minion.Id,
            "Ip": minion.Ip,
            "Port": minion.Port,
            "Status": minion.Status,
            "LastSeen": minion.LastSeen
        }
        for minion in minions
    ]


@app.post("/add-new-hashes")
async def add_new_hashes(hashes: List[str], background_tasks: BackgroundTasks):
    master = get_master_cracker()
    if not hashes or not isinstance(hashes, list):
        raise HTTPException(status_code=400, detail="Invalid input: Expected a list of hash strings")

    count = master.add_new_hashes(hashes)
    jobs_created = master.create_new_job_assignments()
    background_tasks.add_task(master.send_jobs_to_available_minions)

    return {
        "status": "success",
        "message": f"Added {count} new hashes and created {jobs_created} jobs",
        "hashes_added": count,
        "jobs_created": jobs_created
    }


@app.post("/crack-result")
def crack_result(crack_result: CrackResult):
    master = get_master_cracker()
    master.complete_job_assignment(crack_result)
    return {"status": "success"}


@app.get("/get-hash-reports")
def get_hash_reports():
    master = get_master_cracker()
    hash_reports = master.get_hash_reports()
    
    return [report.to_dict() for report in hash_reports]


def main():
    global master_cracker
    master_cracker = MasterCracker()

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT)


if __name__ == '__main__':
    main()