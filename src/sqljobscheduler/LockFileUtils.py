from pathlib import Path
from datetime import datetime
import getpass
import os
import time
from typing import Literal, Optional, Dict
import json

GPU_LOCK_FILE = "/tmp/gpu_lock.json"


def check_gpu_lock_file() -> bool:
    """Check if GPU lock file exists."""
    return Path(GPU_LOCK_FILE).exists()


def gpu_lock_check_timer(duration: int = 600) -> None:
    """Check if GPU lock file exists and sleep for a given duration if it does."""
    while check_gpu_lock_file():
        print(
            f"GPU lock file found. Will sleep for {int(duration / 60)} minutes before checking again."
        )
        time.sleep(duration)


def remove_gpu_lock_file() -> bool:
    if check_gpu_lock_file():
        Path(GPU_LOCK_FILE).unlink()
        print("GPU lock file removed")
        return True
    return False


def create_gpu_lock_file(
    user: str,
    script: str,
    pid: int,
    ctype: Literal["cli", "sql"] = "cli",
    job_id: Optional[str] = None,
) -> bool:
    if check_gpu_lock_file():
        print("GPU lock file already exists")
        return False

    GPU_LOCK_DICT = {
        "user": user,
        "time started": datetime.now().isoformat(),
        "script": script,
        "pid": pid,
        "ctype": ctype,
        "job_id": job_id,
    }

    Path(GPU_LOCK_FILE).touch()
    with open(GPU_LOCK_FILE, "w") as f:
        json.dump(GPU_LOCK_DICT, f, indent=2)

    return True


def get_current_gpu_job() -> Optional[Dict]:
    """Get information about currently running GPU job"""
    if not check_gpu_lock_file():
        print("No GPU job currently running")
        return None

    try:
        with open(GPU_LOCK_FILE, "r") as f:
            lock_info = json.load(f)

        print("\nCurrent GPU Job:")
        print(f"Time started: {lock_info['time started']}")
        print(f"User: {lock_info['user']}")
        print(f"Script: {lock_info['script']}")
        print(f"PID: {lock_info['pid']}")
        print(f"Type: {lock_info['ctype']}")
        if lock_info.get("job_id"):
            print(f"Job ID: {lock_info['job_id']}")

        return lock_info
    except Exception as e:
        print(f"Error reading GPU lock file: {e}")
        return None


def lock_file_argparser():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from_sql",
        action="store_true",
        help="Whether script is being run from SQL scheduler",
    )

    args, unknown = parser.parse_known_args()
    return args


def main():
    print(get_current_gpu_job())


if __name__ == "__main__":
    main()
