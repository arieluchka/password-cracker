# Minion-related queries
create_minions_table = """
CREATE TABLE IF NOT EXISTS minions (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Ip TEXT NOT NULL,
    Port INTEGER NOT NULL,
    Status TEXT DEFAULT 'Available',
    LastSeen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FailedHealthChecks INTEGER DEFAULT 0,
    UNIQUE(Ip, Port)
)
"""

check_minions_table_exists = """
SELECT name FROM sqlite_master WHERE type='table' AND name='minions'
"""

check_minion_exists = """
SELECT Id FROM minions WHERE Ip = ? AND Port = ?
"""

insert_minion = """
INSERT INTO minions (Ip, Port, Status) VALUES (?, ?, 'Available')
"""

get_all_minions = """
SELECT Id, Ip, Port, Status, FailedHealthChecks FROM minions
"""

get_minion_by_id = """
SELECT Id, Ip, Port, Status, LastSeen, FailedHealthChecks FROM minions WHERE Id = ?
"""

update_failed_checks_to_zero = """
UPDATE minions SET FailedHealthChecks = 0, LastSeen = CURRENT_TIMESTAMP WHERE Id = ?
"""

update_minion_status_and_failed_checks = """
UPDATE minions SET Status = ?, FailedHealthChecks = ?, LastSeen = CURRENT_TIMESTAMP WHERE Id = ?
"""

update_minion_status_and_failed_checks_no_lastseen = """
UPDATE minions SET Status = ?, FailedHealthChecks = ? WHERE Id = ?
"""

update_minion_failed_checks = """
UPDATE minions SET FailedHealthChecks = ? WHERE Id = ?
"""

get_available_minions = """
SELECT Id, Ip, Port, Status FROM minions 
WHERE Status = 'Available' AND FailedHealthChecks < ?
"""

update_minion_status = """
UPDATE minions SET Status = ? WHERE Id = ?
"""

# Hash-related queries
create_password_hashes_table = """
CREATE TABLE IF NOT EXISTS password_hashes (
    HashId INTEGER PRIMARY KEY AUTOINCREMENT,
    HashValue TEXT NOT NULL,
    Password TEXT NOT NULL,
    Status TEXT DEFAULT 'Scheduled',
    CreationTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CrackTime TIMESTAMP,
    UNIQUE(HashValue, Password)
)
"""

check_password_hashes_table_exists = """
SELECT name FROM sqlite_master WHERE type='table' AND name='password_hashes'
"""

insert_hash = """
INSERT OR IGNORE INTO password_hashes (HashValue, Password, Status) 
VALUES (?, ?, 'Scheduled')
"""

check_hash_exists = """
SELECT HashId FROM password_hashes WHERE HashValue = ? AND Password = ?
"""

get_scheduled_hashes = """
SELECT HashId, HashValue, Password FROM password_hashes 
WHERE Status = 'Scheduled' 
ORDER BY CreationTime ASC
"""

update_hash_status = """
UPDATE password_hashes SET Status = ?, CrackTime = CURRENT_TIMESTAMP 
WHERE HashId = ?
"""

update_hash_with_password = """
UPDATE password_hashes SET Password = ?, Status = 'Cracked', CrackTime = CURRENT_TIMESTAMP 
WHERE HashId = ?
"""

get_hash_by_id = """
SELECT HashId, HashValue, Password, Status, CreationTime, CrackTime
FROM password_hashes
WHERE HashId = ?
"""

get_hash_by_value = """
SELECT HashId, HashValue, Password, Status, CreationTime, CrackTime
FROM password_hashes
WHERE HashValue = ?
"""

# Job assignment-related queries
create_job_assignments_table = """
CREATE TABLE IF NOT EXISTS job_assignments (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    HashId INTEGER NOT NULL,
    MinionId INTEGER DEFAULT NULL,
    StartRange TEXT NOT NULL,
    EndRange TEXT NOT NULL,
    Status TEXT DEFAULT 'Scheduled',
    AssignmentTime TIMESTAMP,
    CompletionTime TIMESTAMP,
    FOREIGN KEY (HashId) REFERENCES password_hashes(HashId),
    FOREIGN KEY (MinionId) REFERENCES minions(Id)
)
"""

check_job_assignments_table_exists = """
SELECT name FROM sqlite_master WHERE type='table' AND name='job_assignments'
"""

create_job_assignment = """
INSERT INTO job_assignments (HashId, StartRange, EndRange, Status) 
VALUES (?, ?, ?, 'Scheduled')
"""

get_scheduled_job_assignments = """
SELECT Id, HashId, StartRange, EndRange 
FROM job_assignments 
WHERE Status = 'Scheduled' 
ORDER BY Id ASC
LIMIT ?
"""

get_inprogress_job_assignments_with_hashes = """
SELECT 
    job_assignments.Id, 
    job_assignments.HashId, 
    job_assignments.MinionId, 
    job_assignments.StartRange, 
    job_assignments.EndRange,
    password_hashes.HashValue
FROM job_assignments
JOIN password_hashes ON job_assignments.HashId = password_hashes.HashId
WHERE job_assignments.Status = 'InProgress'
"""

update_job_assignment = """
UPDATE job_assignments SET MinionId = ?, Status = ?, AssignmentTime = CURRENT_TIMESTAMP 
WHERE Id = ?
"""

complete_job_assignment = """
UPDATE job_assignments SET Status = 'Completed', CompletionTime = CURRENT_TIMESTAMP 
WHERE Id = ?
"""

get_job_assignment = """
SELECT Id, HashId, MinionId, StartRange, EndRange, Status 
FROM job_assignments 
WHERE HashId = ? AND StartRange = ? AND EndRange = ?
"""

delete_jobs_by_hash_id = """
DELETE FROM job_assignments WHERE HashId = ?
"""

mark_job_assignment_completed = """
UPDATE job_assignments SET Status = 'Completed', CompletionTime = CURRENT_TIMESTAMP 
WHERE Id = ?
"""

reschedule_inprogress_jobs_for_minion = """
UPDATE job_assignments SET Status = 'Scheduled', MinionId = NULL, AssignmentTime = NULL 
WHERE MinionId = ? AND Status = 'InProgress'
"""

