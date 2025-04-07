import os
import subprocess
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqljobscheduler import JobManager
from sqljobscheduler import LockFileUtils
from sqljobscheduler import configSetup

app = FastAPI(title="GPU Job Scheduler Dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Get the TSX output directory
TSX_OUTPUT_DIR = PROJECT_ROOT / "frontend4JL" / "dist"

# Mount static files
app.mount(
    "/dist",
    StaticFiles(directory=str(TSX_OUTPUT_DIR)),
    name="dist",
)
app.mount(
    "/assets",
    StaticFiles(directory=str(TSX_OUTPUT_DIR / "assets")),
    name="assets",
)
app.mount(
    "/docs",
    StaticFiles(directory=str(PROJECT_ROOT / "docs")),
    name="docs",
)

# Constants
DB_PATH = configSetup.get_queue_db_path()


def get_current_time():
    return datetime.now().strftime("%m/%d/%Y %H:%M")


def read_output_file(file_path: Path) -> str:
    try:
        result = subprocess.run(
            ["/usr/bin/cat", str(file_path)], capture_output=True, text=True
        )
        return result.stdout
    except FileNotFoundError:
        return "Error: File not found"


def _get_job_runner_logs() -> List[Path]:
    """Get all job runner logs sorted by modification time

    Returns:
        List[Path]: List of job runner log files sorted by modification time. [0] is the most recent log file.
    """
    log_dir = configSetup.get_log_dir() / "job_runner"
    if not log_dir.exists():
        print(f"Directory does not exist: {log_dir}")
        return []

    log_files = list(log_dir.glob("JR_*.log"))

    return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)


def _get_job_runner_log_dates() -> List[datetime]:
    """Get the modification dates of all job runner log files

    Returns:
        List[datetime]: List of modification dates sorted by modification time. [0] is the most recent log file.
    """
    log_files = _get_job_runner_logs()
    log_files = [os.path.basename(f) for f in log_files]
    dates = []
    for f in log_files:
        components = str(f).split("_")
        dates.append(components[1].split(".")[0])
    return [datetime.strptime(date, "%Y%m%d").date() for date in dates]


def read_job_runner_log(log_idx: int = 0) -> Optional[str]:
    """Read the job runner log file at the given index

    Args:
        log_idx (int, optional): Index of the log file to read. Defaults to 0, which selects the most recent log file.

    Returns:
        Optional[str]: Content of the log file or None if the file does not exist
    """

    log_files = _get_job_runner_logs()
    if not log_files:
        return None

    log_file2read = log_files[log_idx]
    if log_file2read.exists():
        return read_output_file(log_file2read)
    return None


async def get_current_job_output() -> dict:
    tmux4WA_dir = configSetup.get_log_dir() / "tmux4WA"
    tmux4WA_dir.mkdir(parents=True, exist_ok=True)
    current_job_log = tmux4WA_dir / "current_job"

    if LockFileUtils.check_gpu_lock_file():
        lock_info = LockFileUtils.get_current_gpu_job(verbose=False)
        if lock_info["ctype"] == "sql":
            try:
                result = subprocess.run(
                    [
                        "/usr/bin/tmux",
                        "-S",
                        f"/tmp/tmux-{os.getuid()}/gpuJobRunner",
                        "capture-pane",
                        "-t",
                        f"job_{lock_info['job_id']:05d}",
                        "-p",
                        "-S",
                        "-",
                    ],
                    capture_output=True,
                    text=True,
                )
                current_job_log.write_text(result.stdout)
                return {
                    "job_id": lock_info["job_id"],
                    "content": read_output_file(current_job_log),
                    "type": "sql",
                    "error": None,
                }
            except Exception as e:
                return {"error": f"Failed to capture tmux output: {e}", "type": "sql"}
        else:
            return {
                "error": "CLI job currently running. Cannot display output",
                "type": "cli",
            }
    else:
        if current_job_log.exists():
            current_job_log.unlink()
        return {"error": "No job currently running", "type": "none"}


def shorten_path(path_str: str, parts: int = 3) -> str:
    return str(Path(*Path(path_str).parts[-parts:]))


def get_basename(path_str: str) -> str:
    return Path(path_str).name


@app.get("/")
async def read_root():
    return FileResponse(str(TSX_OUTPUT_DIR / "index.html"))


@app.get("/api/gpu-status")
async def get_gpu_status():
    if LockFileUtils.check_gpu_lock_file():
        lock_info = LockFileUtils.get_current_gpu_job(verbose=False)
        if lock_info:
            return {
                "status": "in_use",
                "user": lock_info["user"],
                "script": get_basename(lock_info["script"]).replace(".py", ""),
                "started": lock_info["time started"],
                "pid": lock_info["pid"],
                "type": lock_info["ctype"],
                "job_id": lock_info.get("job_id"),
            }
    return {"status": "available"}


def mask_email(email: str) -> str:
    """Mask an email address for privacy.
    Example: 'ahuro12293@gmail.com' -> 'a********@gmail.com'
    """
    if not email or "@" not in email:
        return email

    local_part, domain = email.split("@")
    if len(local_part) > 1:
        masked_local = local_part[0] + "*" * (len(local_part) - 1)
    else:
        masked_local = local_part

    return f"{masked_local}@{domain}"


@app.get("/api/jobs")
async def get_jobs():
    try:
        queue = JobManager.JobQueue(DB_PATH)
        jobs = queue.get_all_jobs()
        if not jobs:
            return []

        jobs_data = [
            {
                "id": f"{job.id:05d}",
                "program": get_basename(job.programPath).replace(".py", ""),
                "python_exec": shorten_path(job.path2python_exec),
                "user": job.user,
                "email": mask_email(job.email_address),
                "status": job.status.value,
                "created": job.created_at.strftime("%Y-%m-%d %H:%M"),
                "started": job.started_at.strftime("%Y-%m-%d %H:%M")
                if job.started_at
                else "-",
                "completed": job.completed_at.strftime("%Y-%m-%d %H:%M")
                if job.completed_at
                else "-",
                "error": (job.error_message[:50] + "...")
                if job.error_message and len(job.error_message) > 50
                else job.error_message or "-",
            }
            for job in jobs
        ]

        return jobs_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@app.get("/api/job-runner-log")
async def get_job_runner_log():
    log_files = _get_job_runner_logs()  # Already sorted by date
    if not log_files:
        raise HTTPException(status_code=404, detail="No log files found")

    # Get the dates for all available logs
    dates = _get_job_runner_log_dates()

    return {
        "log_files": [log_file.name for log_file in log_files],
        "content": [read_output_file(log_file) for log_file in log_files],
        "availableDates": dates,
    }


@app.delete("/api/remove_job_logs")
async def remove_job_logs():
    try:
        log_files = _get_job_runner_logs()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        basename4log_files = [os.path.basename(f) for f in log_files]
        removed_count = 0

        for idx, log_file in enumerate(basename4log_files):
            # Get date from filename (JR_YYYYMMDD.log)
            date_str = str(log_file).split("_")[1].split(".")[0]
            log_date = datetime.strptime(date_str, "%Y%m%d").date()

            if log_date < week_ago:
                try:
                    log_files[idx].unlink()
                    removed_count += 1
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "error": f"Failed to delete log file {log_file}: {str(e)}",
                            "removed_count": removed_count,
                        },
                    )
        result = {
            "message": f"Successfully removed {removed_count} old log files"
            if removed_count > 0
            else "No old log files to remove",
            "removed_count": removed_count,
        }
        print(result)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during log cleanup: {str(e)}"
        )


@app.get("/api/current-job")
async def get_current_job():
    return await get_current_job_output()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
