import os
import signal
import subprocess


def get_runner_pid():
    """Get the PID of the running JobRunner"""
    try:
        result = subprocess.run(
            "pgrep -f 'python.*JobRunner.py'",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            if len(pids) > 1:
                print(f"Multiple JobRunner processes found: {pids}")
                print(f"Using the first one: {pids[0]}")
            return pids[0]
    except Exception as e:
        print(f"Failed to get JobRunner PID: {e}")
        return None


def main():
    pid = get_runner_pid()
    if pid is None:
        print("JobRunner is not running")
        return

    try:
        os.kill(int(pid), signal.SIGUSR1)
        print("Sent pause/resume signal to JobRunner")
    except Exception as e:
        print(f"Failed to send signal: {e}")


if __name__ == "__main__":
    main()
