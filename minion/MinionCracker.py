import os
from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
import logging
from common.crack_objects import PhoneNumberValidator
import uvicorn
import hashlib
from common.crack_objects import HashEntry
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import requests
from common.crack_objects import CrackRequest, CrackResult
from minion.minion_cracker_db.MinionCrackerDb import MinionCrackerDb
from common.crack_objects.CrackStatus import CrackStatus
from common.models.statuses.MinionStatus import MinionStatus
import os.path
import threading
import socket
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='minion_cracker.log',
    filemode='a'
)
logger = logging.getLogger("MinionCracker")

class MinionCracker:
    def __init__(self, db_path=None, api_port=None, master_ip=None, master_port=None, hash_type=None):
        self.logger = logging.getLogger("MinionCracker")
        self.db_path = db_path or os.environ.get("MINION_DB_PATH") or os.path.join(os.path.dirname(__file__), "MinionCracker.db")
        self.api_port = api_port or int(os.getenv("API_PORT", "8000"))
        self.master_ip = master_ip or "127.0.0.1"
        self.master_port = master_port or 5000
        self.hash_type = hash_type or "md5"
        self.max_workers = multiprocessing.cpu_count()
        self.db = MinionCrackerDb(self.db_path)
        self.active_job = None

    def get_hashlib_func(self, hash_type: str):
        if hash_type.lower() == 'md5':
            return hashlib.md5
        elif hash_type.lower() == 'sha1':
            return hashlib.sha1
        elif hash_type.lower() == 'sha256':
            return hashlib.sha256
        elif hash_type.lower() == 'sha512':
            return hashlib.sha512
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")

    def calculate_hash(self, password):
        return self.get_hashlib_func(self.hash_type)(password.encode('utf-8')).hexdigest()

    def generate_phone_range(self, start_phone: PhoneNumberValidator, end_phone: PhoneNumberValidator) -> List[str]:
        return list(PhoneNumberValidator.range(start_phone, end_phone))

    def distribute_password_list_to_sub_jobs(self, password_list) -> List[List[str]]:
        return [password_list]

    def hash_password(self, password: str, needed_hashes: List[str]):
        password_hash = self.calculate_hash(password=password)
        if password_hash in needed_hashes:
            return HashEntry(hash=password_hash, password=password)

    def multi_processing_sub_job(self, password_list, needed_hashes: List[str], max_workers: int):
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.hash_password, password, needed_hashes) for password in password_list]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
        return results

    def multi_processing_job(self, password_list, needed_hashes: List[str], max_workers: int=None):
        if max_workers is None:
            max_workers = self.max_workers
        sub_jobs = self.distribute_password_list_to_sub_jobs(password_list)
        found_hashes: List[HashEntry] = []
        for sub_job in sub_jobs:
            results = self.multi_processing_sub_job(sub_job, needed_hashes=needed_hashes, max_workers=max_workers)
            found_hashes.extend(results)
        results = {found_hash.hash: found_hash.password for found_hash in found_hashes}
        for needed_hash in needed_hashes:
            if needed_hash not in results:
                results[needed_hash] = False
        return results

    def report_crack_result_to_master(self, results, crack_request: CrackRequest):
        try:
            crack_result = CrackResult(
                range_start=crack_request.start_range,
                range_end=crack_request.end_range,
                results=results,
            )
            response = requests.post(
                f"http://{self.master_ip}:{self.master_port}/crack-result",
                json=crack_result.model_dump()
            )
            response.raise_for_status()
            self.logger.info(f"Successfully reported results to master for range {crack_request.start_range} to {crack_request.end_range}")
            return response.json()
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Failed to report results to master (connection error): {str(e)}")
            return {"status": "error", "message": "Master server unavailable"}
        except Exception as e:
            self.logger.error(f"Failed to report results to master: {str(e)}")
            return {"status": "error", "message": f"Error reporting to master: {str(e)}"}

    def background_crack(self, crack_request: CrackRequest):
        try:
            self.active_job = crack_request
            for hash_value in crack_request.hashes:
                hash_id = self.db.check_hash_exists(hash_value)
                if not hash_id:
                    hash_id = self.db.add_new_hash(hash_value)
                existing_job = self.db.get_hash_job_by_hash_and_range(
                    hash_value, 
                    str(crack_request.start_range), 
                    str(crack_request.end_range)
                )
                if not existing_job:
                    self.db.add_hash_job(hash_id, str(crack_request.start_range), str(crack_request.end_range))
            phone_range = self.generate_phone_range(
                start_phone=crack_request.start_range,
                end_phone=crack_request.end_range
            )
            results = self.multi_processing_job(
                password_list=phone_range,
                needed_hashes=crack_request.hashes,
                max_workers=self.max_workers
            )
            for hash_value, password in results.items():
                hash_info = self.db.get_hash_by_value(hash_value)
                if hash_info and password:
                    self.db.add_password_to_hash(hash_info["Id"], password)
                job = self.db.get_hash_job_by_hash_and_range(
                    hash_value, 
                    str(crack_request.start_range), 
                    str(crack_request.end_range)
                )
                if job:
                    self.db.update_hash_job_status(job.Id, "Completed")
            self.active_job = None
            self.report_crack_result_to_master(results, crack_request)
            return results
        except Exception as e:
            self.logger.error(f"Error in background crack: {e}")
            self.active_job = None
            self.logger.error(f"Background crack job failed: {str(e)}")

    def check_minion_running(self, port=None): # do we really need it? api server wont run if port is occupied..
        port = port or self.api_port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            s.close()
            if result == 0:
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=1)
                    if response.status_code == 200:
                        return True
                except:
                    pass
            return False
        except:
            return False

    def start_up(self):
        if self.check_minion_running():
            self.logger.error(f"Another minion is already running on port {self.api_port}. Exiting.")
            raise SystemExit(f"Error: Another minion is already running on port {self.api_port}")
        if not os.path.exists(self.db_path) or not self.db.check_tables_exist():
            self.logger.info("Creating database tables...")
            self.db.create_tables()
            return
        unfinished_jobs = self.db.get_unfinished_jobs()
        if unfinished_jobs:
            self.logger.info(f"Found {len(unfinished_jobs)} unfinished jobs. Resuming first job...")
            job = unfinished_jobs[0]
            hash_info = self.db.get_hash_by_value(job.HashValue)
            if hash_info:
                crack_request = CrackRequest(
                    hashes=[job.HashValue],
                    start_range=PhoneNumberValidator(phone_number=job.StartRange),
                    end_range=PhoneNumberValidator(phone_number=job.EndRange)
                )
                self.active_job = crack_request
                thread = threading.Thread(target=self.background_crack, args=(crack_request,), daemon=True)
                thread.start()

# FastAPI app and endpoints outside the class
app = FastAPI()
minion_cracker = None

def get_minion_cracker():
    global minion_cracker
    if minion_cracker is None:
        minion_cracker = MinionCracker()
    return minion_cracker

@app.post("/crack")
async def crack(crack_request: CrackRequest, background_tasks: BackgroundTasks):
    minion = get_minion_cracker()
    if minion.active_job:
        minion.logger.warning(
            f"Rejected crack request: another job is already in progress. "
            f"Active job details: hashes={minion.active_job.hashes}, "
            f"range={minion.active_job.start_range} to {minion.active_job.end_range}, "
            f"New request: hashes={crack_request.hashes}, "
            f"range={crack_request.start_range} to {crack_request.end_range}"
        )
        raise HTTPException(status_code=409, detail="A job is already in progress")
    minion.logger.info(f"Received crack request for {len(crack_request.hashes)} hashes. Range: {crack_request.start_range} to {crack_request.end_range}")
    background_tasks.add_task(minion.background_crack, crack_request)
    return {"status": "accepted", "message": "Cracking job started"}

@app.get("/health")
async def health_check():
    minion = get_minion_cracker()
    if minion.active_job:
        return {"status": MinionStatus.BUSY, "timestamp": datetime.now().isoformat()}
    else:
        return {"status": MinionStatus.AVAILABLE, "timestamp": datetime.now().isoformat()}

@app.get("/status/{hash_value}/{start_range}/{end_range}")
async def get_status(hash_value: str, start_range: str, end_range: str):
    minion = get_minion_cracker()
    minion.logger.debug(f"Status check for hash: {hash_value}, range: {start_range} to {end_range}")
    job = minion.db.get_hash_job_by_hash_and_range(hash_value, start_range, end_range)
    if not job:
        minion.logger.warning(f"Status check failed: Job not found for hash: {hash_value}, range: {start_range} to {end_range}")
        raise HTTPException(status_code=404, detail="Job not found")
    hash_info = minion.db.get_hash_by_value(hash_value)
    if not hash_info:
        minion.logger.warning(f"Status check failed: Hash not found: {hash_value}")
        raise HTTPException(status_code=404, detail="Hash not found")
    status = CrackStatus(
        status=job.Status,
        hashes={hash_value: hash_info["Password"] if hash_info["Password"] else False}
    )
    if minion.active_job and minion.active_job.hashes and hash_value in minion.active_job.hashes:
        if start_range == str(minion.active_job.start_range) and end_range == str(minion.active_job.end_range):
            status.status = "InProgress"
    minion.logger.debug(f"Status for hash {hash_value}: {status.status}")
    return status

def main():
    import sys
    parser = argparse.ArgumentParser(description="MinionCracker Service")
    parser.add_argument('--db-path', type=str, help='Path to the minion database file')
    args = parser.parse_args()

    global minion_cracker
    minion_cracker = MinionCracker(db_path=args.db_path)
    try:
        minion_cracker.start_up()
        uvicorn.run(app, host="0.0.0.0", port=minion_cracker.api_port)
    except Exception as e:
        minion_cracker.logger.error(f"Failed to start MinionCracker: {e}")
        sys.exit(1)

def main2():
    NEEDED_HASHES = [
        "e39be3cad2f7b8eda3a80d67bd4412f4",
        "d49f90138f81a1bcef888bd11bd41555",
        "f5a07157040fd1ae5a7a3bb48c90d713",
        "87d6a470856a83b0886c721da7e213d7",
        "393a180472b1cd5d8a37c7efa27a3a2d"
    ]
    DEFAULT_START_PHONE = PhoneNumberValidator(phone_number="052-7500000")
    DEFAULT_END_PHONE = PhoneNumberValidator(phone_number="052-7501999")

    minion_cracker = MinionCracker()
    pass_list = minion_cracker.generate_phone_range(
        start_phone=DEFAULT_START_PHONE,
        end_phone=DEFAULT_END_PHONE
    )

    return minion_cracker.multi_processing_job(
        password_list=pass_list,
        needed_hashes=NEEDED_HASHES
    )

if __name__ == '__main__':
    import sys
    main()