import os
import base64
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqljobscheduler import JobManager
from sqljobscheduler.LockFileUtils import check_gpu_lock_file, get_current_gpu_job

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
TSX_OUTPUT_DIR = PROJECT_ROOT / "frotend4JL" / "dist"

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
DB_PATH = PROJECT_ROOT / "queueDB" / "analysis_jobs.db"


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


def read_job_runner_log() -> Optional[str]:
    log_dir = PROJECT_ROOT / "logs" / "job_runner"
    if not log_dir.exists():
        return None

    log_files = list(log_dir.glob("JR_*.log"))
    if not log_files:
        return None

    log_file = max(log_files, key=lambda x: x.stat().st_mtime)
    if log_file and log_file.exists():
        return read_output_file(log_file)
    return None


async def get_current_job_output() -> dict:
    tmux4WA_dir = PROJECT_ROOT / "logs" / "tmux4WA"
    tmux4WA_dir.mkdir(parents=True, exist_ok=True)
    current_job_log = tmux4WA_dir / "current_job"

    if check_gpu_lock_file():
        lock_info = get_current_gpu_job(verbose=False)
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
                    "output": read_output_file(current_job_log),
                    "type": "sql",
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
    return FileResponse(str(PROJECT_ROOT / "frontend" / "dist" / "index.html"))


@app.get("/api/gpu-status")
async def get_gpu_status():
    if check_gpu_lock_file():
        lock_info = get_current_gpu_job(verbose=False)
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


@app.get("/api/jobs")
async def get_jobs(status: Optional[List[str]] = None):
    try:
        queue = JobManager.JobQueue(DB_PATH)
        jobs = queue.get_all_jobs()
        if not jobs:
            return []

        today = datetime.now()
        filtered_jobs = [
            job
            for job in jobs
            if job.status == JobManager.JobStatus.PENDING
            or job.created_at.date() == today.date()
        ]

        if not filtered_jobs:
            return []

        jobs_data = [
            {
                "id": f"{job.id:05d}",
                "program": get_basename(job.programPath).replace(".py", ""),
                "python_exec": shorten_path(job.path2python_exec),
                "user": job.user,
                "email": job.email_address,
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
            for job in filtered_jobs
        ]

        if status:
            jobs_data = [job for job in jobs_data if job["status"] in status]

        return jobs_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@app.get("/api/job-runner-log")
async def get_job_runner_log():
    log_content = read_job_runner_log()
    if log_content is None:
        raise HTTPException(status_code=404, detail="No Job Runner logs found")
    return {"content": log_content}


@app.get("/api/current-job")
async def get_current_job():
    return await get_current_job_output()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
