# API Usage Guide

This guide covers the main API components of SQLJobScheduler, including email notifications and GPU management.

## Email Configuration

SQLJobScheduler supports email notifications for job status updates. It is best to run this as a CLI to have it set up before being used. Every file is made based on the user who runs the script.

1. Generate email credentials:

```bash
# Run the setup script which will prompt for email configuration
./setup.sh
```

2. The encrypted credentials file with its respective key will be created at `~/.sqljobscheduler/Credentials/` with the following structure:

```json
{
    "email": "your.email@example.com",
    "password": "your_app_specific_password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "server_address": "your.server.address",
    "dashboard_url": "http://your.server:port/app_name"
}
```

3. Using email notifications in your code:

```python
import os
from sqljobscheduler.EmailNotifier import EmailNotifier

# Initialize the notifier
notifier = EmailNotifier()

# notify job start
notifier.notify_job_start(
    recipient=job.email_address,
    job_id=job.id,
    script=job.programPath,
    pid=int(os.getpid()),
)

# notify job complete
notifier.notify_job_complete()
# notify job fail
notifier.notify_job_failed()
```

## GPU Management

SQLJobScheduler provides GPU locking functionality to prevent multiple jobs from using the same GPU simultaneously. This is implemented using lock files.

### Basic GPU Lock Usage

```python
import os
import getpass
from pathlib import Path
from sqljobscheduler import LockFileUtils

def main():
    # Check if GPU is available
    if not LockFileUtils.check_gpu_lock_file(

    ):
        print("Creating GPU lock file for this run")
        # inputting defaults
        LockFileUtils.create_gpu_lock_file(
            user=getpass.getuser(),
            script=Path(__file__).name,
            pid=int(os.getpid()),
            ctype="cli", # "cli" is default option
        )
    
    try:
        # Your GPU-intensive code here
        ...
    finally:
        # Always remove the lock file when done
        LockFileUtils.remove_gpu_lock_file()

if __name__ == "__main__":
    main()
```

### CLI vs running as a job from a job database

If you are running a script that handles non-SQL (CLI) or SQL-based executions, you need this line if you wish to adjust or modify based on those conditions:

```python
sql_parser = LockFileUtils.lock_file_argparser()
if not sql_parser.from_sql:
    # anything you want to do for CLI
if sql_parser.from_sql:
    # anything you want to do for SQL-based executions
```

### Best Practices

1. **Always Remove Lock Files**:
   - Use `try`/`finally` blocks to ensure lock files are removed
   - Call `LockFileUtils.remove_gpu_lock_file()` in the `finally` block

2. **Check GPU Availability**:
   - Use `LockFileUtils.check_gpu_lock_file()` before creating new locks
   - Consider using `gpu_lock_check_timer()` for timeouts

3. **Proper Lock File Creation**:
   - Include user information
   - Include script name
   - Include process ID
   - Specify client type ("cli" for command line)

4. **Command Line Integration**:
   - Use `LockFileUtils.lock_file_argparser()` for command line argument parsing
   - Handle SQL vs non-SQL execution paths appropriately
   - Use `parser.parse_known_args()` to handle both SQL and custom arguments:

## Job Runner

The JobRunner component handles the execution of jobs from the SQL database. It runs as a systemd service and continuously monitors for new jobs.

### Basic Usage

```python
from sqljobscheduler.JobRunner import JobRunner

def main():
    # Initialize the job runner
    runner = JobRunner()
    
    # Start the job runner
    runner.run()
```

### Job Runner Features

1. **Continuous Monitoring**:
   - Automatically checks for new jobs in the database
   - Handles job execution and status updates
   - Manages GPU resources for jobs

2. **Email Notifications**:
   - Sends notifications for job status changes
   - Includes job details and execution results
   - Provides dashboard links for job monitoring

3. **Error Handling**:
   - Graceful handling of job failures
   - Automatic retry mechanisms
   - Detailed error logging

## Job Lister

The JobLister provides a web-based dashboard for monitoring and managing jobs. It runs as a systemd service using Streamlit.

### Accessing the Dashboard

1. **Default URL**: `http://<server_ip>:<port>/<app_name>`
   - Example: `http://localhost:8502/gpujobs`

2. **Features**:
   - Real-time job status monitoring
   - Job history and logs
   - GPU utilization tracking
   - Job submission interface

### Customizing the Dashboard

```python
from sqljobscheduler.JobLister_streamlit import JobLister

# Initialize with custom settings
job_lister = JobLister(
    port=8502,
    app_name="gpujobs",
    refresh_interval=30  # seconds
)

# Start the dashboard
job_lister.run()
```

### Dashboard Components

1. **Job Status Table**:
   - Shows active and completed jobs
   - Displays job parameters and execution status
   - Provides filtering and sorting capabilities

2. **GPU Status Panel**:
   - Real-time GPU utilization
   - Memory usage tracking
   - Temperature monitoring

3. **Job Submission Form**:
   - Parameter configuration
   - Priority settings
   - Resource requirements

4. **Log Viewer**:
   - Real-time log updates
   - Error highlighting
   - Log filtering options

### Best Practices

1. **Service Management**:
   - Use systemd for service management
   - Enable automatic restarts
   - Monitor service health

2. **Security**:
   - Configure appropriate access controls
   - Use HTTPS for remote access
   - Implement user authentication

3. **Performance**:
   - Adjust refresh intervals based on load
   - Monitor database connection pool
   - Optimize query performance

4. **Monitoring**:
   - Set up health checks
   - Monitor resource usage
   - Configure alerting for issues
