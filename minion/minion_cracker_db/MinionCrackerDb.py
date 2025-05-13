import sqlite3
from .db_queries import *
from common.models.Hash import Hash
from common.crack_objects.Job import Job


class MinionCrackerDb:
    def __init__(self, db_path="MinionCracker.db"):
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

    def __update_query(self, query, args=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                if args:
                    cursor.execute(query, args)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount
            except sqlite3.Error as e:
                print(f"Error executing update query {query}: {e}")
                return False

    def check_tables_exist(self):
        """Check if all required tables exist in the database"""
        hashes_exists = self.__select_query(check_hashes_table_exists)
        jobs_exists = self.__select_query(check_hash_jobs_table_exists)
        return bool(hashes_exists) and bool(jobs_exists)

    def create_tables(self):
        """Create all required tables if they don't exist"""
        self.__execute_query(create_hashes_table)
        self.__execute_query(create_hash_jobs_table)
        return True

    def add_new_hash(self, hash_value, password=""):
        """Add a new hash to the database, avoiding duplicates"""
        return self.__execute_query(insert_hash, (hash_value, password))
    
    def check_hash_exists(self, hash_value):
        """Check if a hash already exists in the database"""
        result = self.__select_query(check_hash_exists, (hash_value,))
        return result[0][0] if result else None
    
    def add_password_to_hash(self, hash_id, password):
        """Update a hash with its cracked password"""
        return self.__execute_query(update_hash_with_password, (password, hash_id))
    
    def get_all_hashes(self):
        """Get all hashes from the database"""
        rows = self.__select_query(get_all_hashes)
        if not rows:
            return []
        return [{"Id": row[0], "Hash": row[1], "Password": row[2]} for row in rows]
    
    def get_hash_by_value(self, hash_value):
        """Get a hash by its value"""
        rows = self.__select_query(get_hash_by_value, (hash_value,))
        if not rows:
            return None
        row = rows[0]
        return {"Id": row[0], "Hash": row[1], "Password": row[2]}
    
    def add_hash_job(self, hash_id, start_range, end_range):
        """Add a new hash job to the database"""
        try:
            return self.__execute_query(insert_hash_job, (int(hash_id), str(start_range), str(end_range)))
        except (ValueError, TypeError) as e:
            print(f"Error creating hash job: {e}")
            return False
    
    def get_hash_job_by_hash_and_range(self, hash_value, start_range, end_range):
        """Get a hash job by hash value and range"""
        rows = self.__select_query(get_hash_job_by_hash_and_range, (hash_value, str(start_range), str(end_range)))
        if not rows:
            return None
        row = rows[0]
        return Job(
            Id=row[0],
            HashId=row[1],
            StartRange=row[2],
            EndRange=row[3],
            Status=row[4],
            HashValue=row[5]
        )
    
    def update_hash_job_status(self, job_id, status):
        """Update the status of a hash job"""
        return self.__execute_query(update_hash_job_status, (status, job_id))
    
    def get_hash_job_by_id(self, job_id):
        """Get a hash job by its ID"""
        rows = self.__select_query(get_hash_job_by_id, (job_id,))
        if not rows:
            return None
        row = rows[0]
        return Job(
            Id=row[0],
            HashId=row[1],
            StartRange=row[2],
            EndRange=row[3],
            Status=row[4],
            HashValue=row[5]
        )
    
    def delete_jobs_by_hash_id(self, hash_id):
        """Delete all jobs for a specific hash ID"""
        return self.__execute_query(delete_jobs_by_hash_id, (hash_id,))

    def get_unfinished_jobs(self):
        """Get all jobs with InProgress status"""
        rows = self.__select_query(get_unfinished_jobs)
        if not rows:
            return []
        
        return [Job(
            Id=row[0],
            HashId=row[1],
            StartRange=row[2],
            EndRange=row[3],
            Status=row[4],
            HashValue=row[5]
        ) for row in rows]