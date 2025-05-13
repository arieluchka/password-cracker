# Table check queries
check_hashes_table_exists = """
SELECT name FROM sqlite_master 
WHERE type='table' AND name='Hashes';
"""

check_hash_jobs_table_exists = """
SELECT name FROM sqlite_master 
WHERE type='table' AND name='HashJobs';
"""

# Table creation queries
create_hashes_table = """
CREATE TABLE IF NOT EXISTS Hashes (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Hash TEXT NOT NULL UNIQUE,
    Password TEXT
);
"""

create_hash_jobs_table = """
CREATE TABLE IF NOT EXISTS HashJobs (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    HashId INTEGER NOT NULL,
    StartRange TEXT NOT NULL,
    EndRange TEXT NOT NULL,
    Status TEXT DEFAULT 'InProgress',
    FOREIGN KEY (HashId) REFERENCES Hashes(Id)
);
"""

# Hash related queries
insert_hash = """
INSERT OR IGNORE INTO Hashes (Hash, Password)
VALUES (?, ?);
"""

check_hash_exists = """
SELECT Id FROM Hashes
WHERE Hash = ?;
"""

get_all_hashes = """
SELECT Id, Hash, Password FROM Hashes;
"""

update_hash_with_password = """
UPDATE Hashes
SET Password = ?
WHERE Id = ?;
"""

get_hash_by_value = """
SELECT Id, Hash, Password FROM Hashes
WHERE Hash = ?;
"""

# Hash Jobs related queries
insert_hash_job = """
INSERT INTO HashJobs (HashId, StartRange, EndRange)
VALUES (?, ?, ?);
"""

get_hash_job_by_hash_and_range = """
SELECT hj.Id, hj.HashId, hj.StartRange, hj.EndRange, hj.Status, h.Hash
FROM HashJobs hj
JOIN Hashes h ON h.Id = hj.HashId
WHERE h.Hash = ? AND hj.StartRange = ? AND hj.EndRange = ?;
"""

update_hash_job_status = """
UPDATE HashJobs
SET Status = ?
WHERE Id = ?;
"""

get_hash_job_by_id = """
SELECT hj.Id, hj.HashId, hj.StartRange, hj.EndRange, hj.Status, h.Hash
FROM HashJobs hj
JOIN Hashes h ON h.Id = hj.HashId
WHERE hj.Id = ?;
"""

get_unfinished_jobs = """
SELECT hj.Id, hj.HashId, hj.StartRange, hj.EndRange, hj.Status, h.Hash
FROM HashJobs hj
JOIN Hashes h ON h.Id = hj.HashId
WHERE hj.Status = 'InProgress'
"""

delete_jobs_by_hash_id = """
DELETE FROM HashJobs
WHERE HashId = ?;
"""