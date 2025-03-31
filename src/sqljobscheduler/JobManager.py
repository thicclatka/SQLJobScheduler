import os
import signal
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import sqlite3
from typing import Optional, Dict, List
import json
from pathlib import Path
import psutil


def get_JobRunner_pid():
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if "JobRunner.py" in " ".join(proc.info["cmdline"] or []):
            return proc.info["pid"]


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: Optional[int]
    programPath: str
    path2python_exec: str
    parameters: Dict
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: JobStatus
    error_message: Optional[str]
    python_env: Optional[str] = None
    email_address: Optional[str] = None
    user: Optional[str] = None


class JobQueue:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Get the project root directory (three levels up from this file)
            project_root = Path(__file__).parent.parent.parent

            # Use the queueDB directory
            db_dir = project_root / "queueDB"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "analysis_jobs.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(
                "SQLJobScheduler NOTE: Database file not found: Initializing new database."
            )
            self._init_db()

    def _init_db(self):
        """Initialize SQLite database with jobs table"""
        # Ensure directory exists with correct permissions
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Store old umask and set new one (002 allows group write)
        old_umask = os.umask(0o002)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY,
                        programPath TEXT NOT NULL,
                        python_env TEXT,
                        path2python_exec TEXT NOT NULL,
                        parameters TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        email_address TEXT,
                        user TEXT
                    )
                """)

            os.chmod(self.db_path, 0o664)
            shutil.chown(self.db_path, group="admin_group")
        except Exception as e:
            print(f"Error initializing database: {e}")
        finally:
            os.umask(old_umask)

    def add_job(
        self,
        programPath: str,
        path2python_exec: str,
        parameters: Dict,
        email_address: Optional[str] = None,
        user: Optional[str] = None,
        python_env: Optional[str] = None,
    ) -> int:
        """Add a new job to the queue"""

        params_json = json.dumps(parameters)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs 
                (programPath, path2python_exec, parameters, created_at, status, email_address, user, python_env)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    programPath,
                    path2python_exec,
                    params_json,
                    datetime.now(),
                    JobStatus.PENDING.value,
                    email_address,
                    user,
                    python_env,
                ),
            )
            return cursor.lastrowid

    def get_next_pending_job(self) -> Optional[Job]:
        """Get the next pending job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, programPath, path2python_exec, parameters, 
                       created_at, started_at, completed_at, 
                       status, error_message, email_address, user, python_env
                FROM jobs 
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (JobStatus.PENDING.value,),
            ).fetchone()

            if row:
                return Job(
                    **{
                        **dict(row),
                        "parameters": json.loads(row["parameters"]),
                        "created_at": datetime.fromisoformat(row["created_at"]),
                        "started_at": datetime.fromisoformat(row["started_at"])
                        if row["started_at"]
                        else None,
                        "completed_at": datetime.fromisoformat(row["completed_at"])
                        if row["completed_at"]
                        else None,
                        "status": JobStatus(row["status"]),
                        "email_address": row["email_address"],
                        "user": row["user"],
                        "python_env": row["python_env"],
                    }
                )
            return None

    def update_job_status(
        self, job_id: int, status: JobStatus, error_message: Optional[str] = None
    ):
        """Update job status"""
        with sqlite3.connect(self.db_path) as conn:
            if status == JobStatus.RUNNING:
                conn.execute(
                    """
                    UPDATE jobs 
                    SET status = ?, started_at = ?
                    WHERE id = ?
                    """,  # Remove extra comma after error_message
                    (status.value, datetime.now().isoformat(), job_id),
                )
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                conn.execute(
                    """
                    UPDATE jobs 
                    SET status = ?, completed_at = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (status.value, datetime.now().isoformat(), error_message, job_id),
                )

    def get_all_jobs(self) -> List[Job]:
        """Get all jobs in the queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, programPath, path2python_exec, parameters, 
                       created_at, started_at, completed_at, 
                       status, error_message, email_address, user, python_env
                FROM jobs 
                ORDER BY created_at DESC
                """
            ).fetchall()
            return [
                Job(
                    **{
                        **dict(row),
                        "parameters": json.loads(row["parameters"]),
                        "created_at": datetime.fromisoformat(row["created_at"]),
                        "started_at": datetime.fromisoformat(row["started_at"])
                        if row["started_at"]
                        else None,
                        "completed_at": datetime.fromisoformat(row["completed_at"])
                        if row["completed_at"]
                        else None,
                        "status": JobStatus(row["status"]),
                        "email_address": row["email_address"],
                        "user": row["user"],
                        "python_env": row["python_env"],
                    }
                )
                for row in rows
            ]

    def clear_db(self):
        """Clear all jobs from the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs")
            conn.commit()
        print("Database cleared successfully")


def main(args):
    if args.clearJobs:
        queue = JobQueue()
        queue.clear_db()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clearJobs",
        default=True,
        help="Clear all jobs from the database",
        type=bool,
    )
    args = parser.parse_args()

    main(args)
