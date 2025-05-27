import argparse
from datetime import datetime, timedelta
from pathlib import Path

from tabulate import tabulate

from sqljobscheduler.configSetup import get_queue_db_path
from sqljobscheduler.JobManager import JobQueue


def shorten_path(path_str: str, parts: int = 3) -> str:
    """Shorten a path to show only the last N parts"""
    return str(Path(*Path(path_str).parts[-parts:]))


def get_basename(path_str: str) -> str:
    """Get the basename of a path"""
    return Path(path_str).name


def main(args):
    # Use the data directory for the database
    db_path = get_queue_db_path()

    queue = JobQueue(str(db_path))
    jobs = queue.get_all_jobs()

    # Filter jobs based on status and days
    if args.status:
        jobs = [job for job in jobs if job.status == args.status]
    if args.days:
        cutoff_date = datetime.now() - timedelta(days=args.days)
        jobs = [job for job in jobs if job.created_at >= cutoff_date]

    # Convert jobs to a list of dictionaries for display
    job_rows = []
    for job in jobs:
        job_rows.append(
            {
                "ID": f"{job.id:05d}",
                "Program": get_basename(job.programPath).replace(".py", ""),
                "Python Exec": shorten_path(job.path2python_exec),
                "Python Env": job.python_env if job.python_env is not None else "-",
                "User": job.user,
                "Email": job.email_address,
                "Status": job.status.value,
                "Created": job.created_at.strftime("%Y-%m-%d %H:%M"),
                "Started": job.started_at.strftime("%Y-%m-%d %H:%M")
                if job.started_at
                else "-",
                "Completed": job.completed_at.strftime("%Y-%m-%d %H:%M")
                if job.completed_at
                else "-",
                "Error": (job.error_message[:50] + "...")
                if job.error_message and len(job.error_message) > 50
                else job.error_message or "-",
            }
        )

    if job_rows:
        print(tabulate(job_rows, headers="keys", tablefmt="grid"))
    else:
        print("No jobs found in the queue.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List jobs in the queue")
    parser.add_argument(
        "--status",
        choices=["pending", "running", "completed", "failed"],
        default=None,
        help="Filter by job status (default: show all statuses)",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Show jobs from the last N days"
    )
    args = parser.parse_args()
    main(args)
