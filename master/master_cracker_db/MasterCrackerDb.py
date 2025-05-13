import sqlite3
from .db_queries import *
from common.models.Minion import Minion
from common.models.JobAssignment import JobAssignment
from common.models.statuses.JobAssignmentStatus import JobAssignmentStatus


class MasterCrackerDbInterface:
    def __init__(self, db_path="MasterCracker.db"):
        self.db_path = db_path

    def __select_query(self, query, args=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                if args:
                    cursor.execute(query, args)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Error executing SELECT query {query}: {e}")
                return False

    def __execute_query(self, query, args=None, commit=True):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                if args:
                    cursor.execute(query, args)
                else:
                    cursor.execute(query)
                if commit:
                    conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as e:
                print(f"Error executing query {query}: {e}")
                return False

    def __update_query(self, query):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query)

                conn.commit()

                return cursor.rowcount

            except sqlite3.Error as e:
                print(f"Error executing update query {query}: {e}")
                return False

    def check_tables_exist(self):
        minions_exists = self.__select_query(check_minions_table_exists)
        hashes_exists = self.__select_query(check_password_hashes_table_exists)
        jobs_exists = self.__select_query(check_job_assignments_table_exists)
        return bool(minions_exists) and bool(hashes_exists) and bool(jobs_exists)

    def create_tables(self):
        self.__execute_query(create_minions_table)
        self.__execute_query(create_password_hashes_table)
        self.__execute_query(create_job_assignments_table)

    def minion_exists(self, ip, port):
        result = self.__select_query(check_minion_exists, (ip, port))
        return result[0][0] if result else None

    def register_new_minion(self, ip, port):
        try:
            return self.__execute_query(insert_minion, (ip, port))
        except sqlite3.IntegrityError:
            return None

    def get_all_available_minions(self, max_failed_checks=3):
        """Get all available minions with failed health checks below threshold"""
        rows = self.__select_query(get_available_minions, (max_failed_checks,))
        if not rows:
            return []
        return [Minion(row[0], row[1], row[2], row[3]) for row in rows]

    def get_all_minions(self):
        rows = self.__select_query(get_all_minions)
        if not rows:
            return []
        return [Minion(*row) for row in rows]

    def get_minion_by_id(self, minion_id):
        row = self.__select_query(get_minion_by_id, (minion_id,))
        if row:
            return Minion(*row[0])
        return None

    def update_failed_checks_to_zero(self, failed_health_checks):
        return self.__execute_query(update_failed_checks_to_zero, (failed_health_checks,))

    def update_minion_status_and_failed_checks(self, minion_id, status, failed_health_checks):
        return self.__execute_query(update_minion_status_and_failed_checks, (status, failed_health_checks, minion_id))

    def update_minion_status_and_failed_checks_no_lastseen(self, minion_id, status, failed_health_checks):
        return self.__execute_query(update_minion_status_and_failed_checks_no_lastseen, (status, failed_health_checks, minion_id))

    def update_minion_failed_checks(self, minion_id, failed_health_checks):
        return self.__execute_query(update_minion_failed_checks, (failed_health_checks, minion_id))

    def add_new_hash(self, hash_value, password=""):
        """Add a new hash to the database, avoiding duplicates"""
        return self.__execute_query(insert_hash, (hash_value, password))
    
    def check_hash_exists(self, hash_value, password=""):
        """Check if a hash already exists in the database"""
        result = self.__select_query(check_hash_exists, (hash_value, password))
        return result[0][0] if result else None
    
    def get_scheduled_hashes(self):
        rows = self.__select_query(get_scheduled_hashes)
        if not rows:
            return []
        return [{"HashId": row[0], "HashValue": row[1], "Password": row[2]} for row in rows]
    
    def update_hash_status(self, hash_id, status):
        """Update the status of a hash"""
        return self.__execute_query(update_hash_status, (status, hash_id))
    
    def update_hash_with_password(self, hash_id, password):
        """Update a hash with its cracked password"""
        return self.__execute_query(update_hash_with_password, (password, hash_id))
    
    def create_job_assignment(self, hash_id, start_range, end_range):
        try:
            return self.__execute_query(create_job_assignment, (int(hash_id), str(start_range), str(end_range)))
        except (ValueError, TypeError) as e:
            print(f"Error creating job assignment: {e}")
            return False
    
    def get_scheduled_job_assignments(self, limit=10):
        """Get job assignments that are scheduled but not yet assigned to a minion"""
        rows = self.__select_query(get_scheduled_job_assignments, (limit,))
        if not rows:
            return []
        return [JobAssignment(
            Id=row[0],
            HashId=row[1],
            StartRange=row[2],
            EndRange=row[3],
            Status=JobAssignmentStatus.SCHEDULED
        ) for row in rows]
    
    def update_job_assignment(self, job_id, minion_id, status="InProgress"):
        """Update a job assignment with minion ID and status"""
        return self.__execute_query(update_job_assignment, (minion_id, status, job_id))
    
    def complete_job_assignment(self, job_id):
        """Mark a job assignment as completed"""
        return self.__execute_query(complete_job_assignment, (job_id,))
    
    def get_job_assignment(self, hash_id, start_range, end_range):
        """Get a job assignment by hash ID and range"""
        # Convert hash_id to int to ensure proper parameter binding
        try:
            hash_id = int(hash_id)
            rows = self.__select_query(get_job_assignment, (hash_id, str(start_range), str(end_range)))
            if not rows:
                return None
            row = rows[0]
            return JobAssignment(
                Id=row[0],
                HashId=row[1],
                MinionId=row[2],
                StartRange=row[3],
                EndRange=row[4],
                Status=JobAssignmentStatus(row[5]) if row[5] else JobAssignmentStatus.SCHEDULED
            )
        except (ValueError, TypeError) as e:
            print(f"Error in get_job_assignment: {e}")
            return None
    
    def delete_jobs_by_hash_id(self, hash_id):
        """Delete all jobs for a specific hash ID"""
        return self.__execute_query(delete_jobs_by_hash_id, (hash_id,))

    def update_minion_status(self, minion_id, status):
        return self.__execute_query(update_minion_status, (status, minion_id))

    def get_hash_by_id(self, hash_id):
        """Get a hash entry by its HashId and return as a Hash model"""
        rows = self.__select_query(get_hash_by_id, (hash_id,))
        if not rows:
            return None
        row = rows[0]
        from common.models.Hash import Hash
        return Hash(
            HashId=row[0],
            HashValue=row[1],
            Password=row[2],
            Status=row[3],
            CreationTime=row[4],
            CrackTime=row[5],
        )

    def batch_create_job_assignments(self, batch_values):
        """
        Create multiple job assignments in a single transaction
        
        Args:
            batch_values: A list of tuples in the format (hash_id, start_range, end_range, status)
        
        Returns:
            Number of job assignments created or False on error
        """
        if not batch_values:
            return 0
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.executemany(create_job_assignment, batch_values)
                rowcount = cursor.rowcount
                conn.commit()
                return rowcount
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error in batch job creation: {e}")
                return False

    def get_hash_by_value(self, hash_value):
        """Get a hash entry by its HashId and return as a Hash model"""
        rows = self.__select_query(get_hash_by_value, (hash_value,))
        if not rows:
            return None
        row = rows[0]
        from common.models.Hash import Hash
        return Hash(
            HashId=row[0],
            HashValue=row[1],
            Password=row[2],
            Status=row[3],
            CreationTime=row[4],
            CrackTime=row[5],
        )

    def mark_job_assignment_completed(self, job_id):
        """Mark a job assignment as completed and set CompletionTime to current time"""
        return self.__execute_query(mark_job_assignment_completed, (job_id,))

    def reschedule_inprogress_jobs_for_minion(self, minion_id):
        """Reschedule all InProgress jobs for a minion (set to Scheduled, MinionId=NULL)"""
        return self.__execute_query(reschedule_inprogress_jobs_for_minion, (minion_id,))

    def get_all_in_progress_jobs(self):
        return self.__select_query(get_inprogress_job_assignments_with_hashes)