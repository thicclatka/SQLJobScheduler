import logging
import time
import os
import signal
from pathlib import Path
from libtmux import Server
from datetime import datetime
from datetime import timedelta
from sqljobscheduler import JobManager
from sqljobscheduler import LockFileUtils
from sqljobscheduler import EmailNotifier
# import argparse


class JobRunner:
    def __init__(self, queue: JobManager.JobQueue, log_dir_str: str = "logs"):
        self.queue = queue
        self.running = False
        self.paused = False
        self.kill = False
        self.notifier = EmailNotifier()
        self.current_log_date = None
        self.pid = os.getpid()
        self.no_job_count = 0

        # Set root directory and log directory
        self.root_dir = Path(__file__).parent.parent.parent
        self.log_dir = self.root_dir / log_dir_str
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup signal handlers
        self._setup_signal_handlers()

        # Setup logging
        self._setup_logging()

        self._init_stats()

    def _init_stats(self) -> None:
        self.stats = {
            "completed": 0,
            "failed": 0,
            "total": 0,
        }

    def _setup_signal_handlers(self):
        """Setup all signal handlers in one place"""
        signal.signal(signal.SIGUSR1, self._toggle_pause)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        # signal.signal(signal.SIGINT, self._handle_shutdown)

    def _setup_logging(self):
        """Setup logging with daily rotation"""
        self.current_log_date = datetime.now().date()
        log_file = (
            self.log_dir
            / "job_runner"
            / f"JR_{self.current_log_date.strftime('%Y%m%d')}.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        if log_file.exists():
            logging.info("Restarting job runner")
        else:
            logging.info(
                f"Starting new log file for {self.current_log_date.strftime('%Y%m%d')}"
            )
            logging.info(f"Log file: {str(log_file)}")
        logging.info(f"Job runner PID: {self.pid}")

    def _check_log_rotation(self):
        """Check if the log file needs to be rotated"""

        def _end_log_file():
            """End the current log file"""
            stats_str = f"Stats: total: {self.stats['total']} | completed: {self.stats['completed']} | failed: {self.stats['failed']}"
            if self.stats["total"] > 0:
                perc_completed = (self.stats["completed"] / self.stats["total"]) * 100
                perc_failed = (self.stats["failed"] / self.stats["total"]) * 100
                perc_str = (
                    f"Completed: {perc_completed:.2f}% | Failed: {perc_failed:.2f}%"
                )
            else:
                perc_str = "No jobs processed"

            logging.info(stats_str)
            logging.info(perc_str)

        if datetime.now().date() != self.current_log_date:
            # End the current log file
            _end_log_file()
            self._init_stats()
            self._setup_logging()

    def run_job(self, job):
        """Run job in a tmux session and wait for completion"""
        # ZSHRC = str(self.root_dir / "ServerService" / "zshrc4jobrunner")
        # zsh_setup = f"exec zsh -f && source {ZSHRC} && clear"

        cmd = []
        if job.python_env is not None:
            # zsh_setup = "exec zsh && sleep 1"
            conda_setup = f"conda activate {job.python_env}"
        else:
            conda_setup = None

        if job.python_env == "caiman":
            conda_setup = f"{conda_setup} && export MKL_NUM_THREADS=1 && export OPENBLAS_NUM_THREADS=1 && export VECLIB_MAXIMUM_THREADS=1"

        cmd.append(job.path2python_exec)
        cmd.append(job.programPath)
        cmd.append("--from_sql")

        # Add parameters
        for key, value in job.parameters.items():
            if value is not None:
                if isinstance(value, str):
                    cmd.append(f"--{key} '{value}'")
                else:
                    cmd.append(f"--{key} {value}")

        session_name = f"job_{job.id:05d}"
        full_cmd = " ".join(cmd)

        tmux_logs = Path(self.log_dir) / "tmux"
        tmux_logs.mkdir(exist_ok=True)
        tmux_log_file = (
            tmux_logs
            / f"tmux_{job.id:05d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        server = Server(socket_path=f"/tmp/tmux-{os.getuid()}/gpuJobRunner")
        LockFileUtils.gpu_lock_check_timer(duration=600)

        if not LockFileUtils.check_gpu_lock_file():
            print("Creating GPU lock file for this script")
            LockFileUtils.create_gpu_lock_file(
                user=job.user,
                script=job.programPath,
                pid=int(self.pid),
                ctype="sql",
                job_id=job.id,
            )

        try:
            # Send email notification that job is starting
            self.notifier.notify_job_start(
                recipient=job.email_address,
                job_id=job.id,
                script=job.programPath,
                pid=int(self.pid),
            )

            # Create new session
            session = server.new_session(
                session_name=session_name,
                kill_session=True,
                attach=False,
            )

            pane = session.active_window.panes[0]

            # Setup session to use a modified zshrc config
            # pane.send_keys(zsh_setup)

            if conda_setup is not None:
                # pane.send_keys(zsh_setup)
                pane.send_keys(conda_setup)

            time.sleep(0.5)
            pane.send_keys("tmux set-option history-limit 1000000")
            time.sleep(0.5)

            # Send the command with error handling
            pane.send_keys(
                f"""
                {full_cmd} && {{
                    echo "Job completed successfully";
                    exit 0;
                    }}|| {{ 
                    echo "Job failed with exit code $?";
                    tmux capture-pane -p -S - > {tmux_log_file};
                    exit 1;
            }}
            """.strip()
            )

            logging.info(f"Started job {job.id} in tmux session: {session_name}")

            # Wait for session to end
            while server.has_session(session_name):
                time.sleep(5)

            if tmux_log_file.exists():
                self.stats["failed"] += 1
                logging.error(f"Job {job.id} failed. See tmux log: {tmux_log_file}")
                self.notifier.notify_job_failed(
                    recipient=job.email_address,
                    job_id=job.id,
                    script=job.programPath,
                    pid=int(self.pid),
                    error=f"Job failed. See tmux log: {tmux_log_file}",
                )
            else:
                self.stats["completed"] += 1
                logging.info(f"Job {job.id} completed successfully")
                self.notifier.notify_job_complete(
                    recipient=job.email_address,
                    job_id=job.id,
                    script=job.programPath,
                    pid=int(self.pid),
                )

        except Exception as e:
            logging.error(
                f"Error in handling wrapper for tmux processing for job {job.id}: {e}"
            )

        finally:
            self.no_job_count = 0
            LockFileUtils.remove_gpu_lock_file()
            logging.info(f"Removed GPU lock file")

    def run_pending_jobs(self) -> None:
        """Process all pending jobs"""
        # Check if the log file needs to be rotated
        self._check_log_rotation()
        logging.info("Starting job processing run")

        try:
            job = self.queue.get_next_pending_job()
            while job and self.running:
                if self.paused:
                    logging.info("Job runner paused. Waiting for resume signal...")
                    return

                if self.kill:
                    logging.info("Received shutdown signal. Exiting.")
                    self.stop()
                    return

                try:
                    self.stats["total"] += 1
                    logging.info(f"Processing job {job.id}: {job.programPath}")
                    logging.info(f"Parameters: {job.parameters}")

                    self.queue.update_job_status(job.id, JobManager.JobStatus.RUNNING)
                    self.run_job(job)
                    self.queue.update_job_status(job.id, JobManager.JobStatus.COMPLETED)

                    logging.info(f"Completed job {job.id}")

                except Exception as e:
                    error_msg = f"Error processing job {job.id}: {str(e)}"
                    logging.error(error_msg)
                    self.queue.update_job_status(
                        job.id, JobManager.JobStatus.FAILED, str(e)
                    )

                job = self.queue.get_next_pending_job()

            if job is None:
                logging.info(
                    "No pending jobs found. Will wait for new jobs to be added."
                )
                self.no_job_count += 1
                return

        except Exception as e:
            logging.error(f"Critical error in job runner: {str(e)}")

    def start(self) -> None:
        """Start the job runner"""
        self.running = True
        logging.info("Job runner started")

    def stop(self) -> None:
        """Stop the job runner"""
        self.running = False
        logging.info("Job runner stopped")

    def _toggle_pause(self, signum, frame) -> None:
        """Toggle pause/resume"""
        self.paused = not self.paused
        state = "PAUSED" if self.paused else "RESUMED"
        logging.info(
            f"Job runner sent {state} signal. Will either pause after current job or will continue to run."
        )

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signal"""
        logging.info("Received shutdown signal. Will stop after current job completes.")
        self.kill = True


def get_next_quarter():
    """Get the next quarter hour"""
    now = datetime.now()
    minutes = now.minute

    if minutes < 15:
        next_quarter = 15
    elif minutes < 30:
        next_quarter = 30
    elif minutes < 45:
        next_quarter = 45
    else:
        next_quarter = 0
        now = now + timedelta(hours=1)

    next_time = now.replace(minute=next_quarter, second=0, microsecond=0)
    return next_time


def get_next_hour(hours: int = 1):
    """Get the next hour"""
    now = datetime.now()
    next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hours)
    return next_time


def main():
    def _print_current_numJobs(num_jobs: int):
        logging.info(f"Current number of jobs to process: {num_jobs}")

    def _get_num_pending_jobs(jobs: list[JobManager.Job]):
        num_pending = 0
        for job in jobs:
            if job.status == JobManager.JobStatus.PENDING:
                num_pending += 1
        return num_pending

    # Initialize queue and runner
    queue = JobManager.JobQueue()
    runner = JobRunner(queue)

    try:
        runner.start()

        while runner.running:
            jobs = queue.get_all_jobs()
            initial_jobs = _get_num_pending_jobs(jobs)

            # Sleep until next quarter hour
            if runner.no_job_count < 3:
                next_time = get_next_hour(hours=1)
            elif runner.no_job_count < 6:
                next_time = get_next_hour(hours=6)
            else:
                next_time = get_next_hour(hours=12)

            sleep_seconds = (next_time - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                time2sleep = (
                    f"{sleep_seconds / 60:.0f} minutes"
                    if sleep_seconds > 60
                    else f"{sleep_seconds:.0f} seconds"
                )
                logging.info(f"Will start processing jobs in {time2sleep}")
                _print_current_numJobs(initial_jobs)

                while datetime.now() < next_time:
                    time.sleep(30)
                    current_jobs = _get_num_pending_jobs(queue.get_all_jobs())
                    if current_jobs > initial_jobs:
                        current_job = queue.get_next_pending_job()
                        user = current_job.user
                        email = current_job.email_address
                        created_at = current_job.created_at
                        logging.info(
                            f"{int(current_jobs - initial_jobs)} job(s) added to queue by {user} ({email}) done at {created_at}"
                        )
                        _print_current_numJobs(current_jobs)
                    elif current_jobs < initial_jobs:
                        logging.info(
                            f"Queue size decreased from {initial_jobs} to {current_jobs}"
                        )
                        if current_jobs == 0:
                            logging.info(
                                "Appears jobs have been cleared. Will wait for new jobs to be added."
                            )
                        _print_current_numJobs(current_jobs)
                    initial_jobs = current_jobs

            runner.run_pending_jobs()
            # Sleep for 1 second, especially for when there are no pending jobs
            # time.sleep(60)
    # except KeyboardInterrupt:
    #     logging.info("Stopping job runner due to keyboard interrupt...")
    finally:
        runner.stop()


if __name__ == "__main__":
    main()
